# -*- coding: utf-8 -*-

# Many times in Material Science, a workflow is made up of other smaller workflows.
# For example, calculations for bandstructure first involve a structure relaxation
# followed by a static energy calculations -- before the bandstructure is even
# calculated.
#
# For this reason, we need a way to call these workflows as if they were a task.
# Prefect has a module prefect.tasks.prefect.flow_run which is close to this
# idea -- but this module requires you to be using Prefect Cloud and have all
# of the flows registered. We need to account for running flows locally too!
# Therefore, we had to make this custom task here. This task can be viewed as
# a fork of prefect's module, where we are merging functionality of
# create_flow_run and wait_for_flow_run into one task AND adding the default
# ability to run things locally. For future development, be sure to keep an
# eye on their task and how it compares:
#   https://github.com/PrefectHQ/prefect/blob/master/src/prefect/tasks/prefect/flow_run.py
#   from prefect.tasks.prefect.flow_run import create_flow_run, wait_for_flow_run

import json
import cloudpickle

import prefect
from prefect import Client, Task
from prefect.backend.flow_run import FlowRunView, FlowView, watch_flow_run
from prefect.utilities.tasks import defaults_from_attrs


class RunWorkflowTask(Task):
    def __init__(
        self,
        # The full workflow to run. This is required to be a Flow object
        workflow,
        # How the workflow should be scheduled and ran. The options are either
        # local or prefect (i.e. prefect cloud).
        executor_type="local",
        # If Prefect is used to schedule the workflow, then this indicates
        # whether we should wait for the flow to finish or not.
        wait_for_run=True,
        # If Prefect is used, these are other kwargs that will be passed into
        # create_flow_run.
        project_name="",
        context=None,
        labels=None,
        run_name=None,
        run_config=None,
        scheduled_start_time=None,
        stream_states=True,
        stream_logs=False,
        # If Prefect is used to schedule the workflow, we also may want to
        # To support other Prefect input options. To see all the options, visit...
        # https://docs.prefect.io/api/latest/core/task.html
        **kwargs,
    ):

        # make sure the user selected a valid option
        if executor_type not in ["local", "prefect"]:
            raise Exception(
                f"{executor_type} is not a valid option! "
                "Please choose between local and prefect"
            )
        # NOTE: We don't support Dask or Simmate executors because this would
        # cause some messy nested parallelization. For example, if the parent
        # workflow is submitted with Dask, this workflow would be submitted as
        # an individual task to that Cluster -- so submitting this child
        # workflow's task to the same Cluster can cause issues. So you should
        # stick to Prefect Cloud for advanced parallelization.

        # Save our inputs
        self.workflow = workflow
        self.executor_type = executor_type
        self.wait_for_run = wait_for_run

        # Save other inputs from original Prefect tasks
        self.project_name = project_name
        self.context = context
        self.labels = labels
        self.run_name = run_name
        self.run_config = run_config
        self.scheduled_start_time = scheduled_start_time
        self.stream_states = stream_states
        self.stream_logs = stream_logs

        # now inherit the parent Prefect Task class
        super().__init__(**kwargs)

    @defaults_from_attrs(
        "executor_type",
        "wait_for_run",
        "project_name",
        "context",
        "labels",
        "run_name",
        "run_config",
        "scheduled_start_time",
        "stream_states",
        "stream_logs",
    )
    def run(
        self,
        executor_type=None,
        wait_for_run=None,
        project_name=None,
        context=None,
        labels=None,
        run_name=None,
        run_config=None,
        scheduled_start_time=None,
        stream_states=None,
        stream_logs=None,
        **parameters,
    ):
        # The kwargs here are any parameter you would normally pass into the
        # workflow.run() method.

        # If we want this ran locally, we can run the workflow directly. We
        # also make sure the workflow is successful -- otherwise we want to
        # raise an error so that this task is flagged as failed
        if executor_type == "local":
            status = self.workflow.run(**parameters)
            if not status.is_successful():
                raise Exception(
                    "The workflow task did not complete successfully. "
                    "View the prefect-logs above for more info."
                )

        # If we are using prefect, we assume that the flow has been registered
        # and simply submit it from here.
        elif executor_type == "prefect":
            # Now create the flow run in the prefect cloud
            flow_run_id = self._create_flow_run_prefect(
                parameters,
                wait_for_run,
                project_name,
                context,
                labels,
                run_name,
                run_config,
                scheduled_start_time,
            )
            # if we want to wait until the job is complete, we do that and
            # also make sure that it completed successfully
            if wait_for_run:
                flow_run_view = self._wait_for_flow_run_prefect(
                    flow_run_id, stream_states, stream_logs
                )
                if not flow_run_view.state.is_successful():
                    raise Exception(
                        "The workflow task did not complete successfully. "
                        "View the prefect-logs above for more info. Because "
                        "you ran this through Prefect Cloud, the flow-run URL "
                        "will give you the most information."
                    )

    def _create_flow_run_prefect(
        self,
        parameters,
        wait_for_run,
        project_name,
        context,
        labels,
        run_name,
        run_config,
        scheduled_start_time,
    ):
        """
        This method is a direct fork of...
            from prefect.tasks.prefect.flow_run import create_flow_run

        It does exactly the same thing except it takes a workflow object instead
        of flow_id/flow_name
        """

        # Grab the logger as we will print useful information below
        logger = prefect.context.logger

        # First, serialize all of the parameters so they can be properly submitted
        parameters_serialized = self._serialize_parameters(parameters)

        # Grab the Flow's ID from Prefect Cloud
        logger.debug("Looking up flow metadata...")
        flow_view = FlowView.from_flow_name(
            self.workflow.name,
            project_name=project_name,
        )

        # Generate a 'sub-flow' run name that is an extension of the workflow
        # that this is ran within. If this task is ran directly and not within
        # a workflow, we just leave it empty and a random name will be generated
        # below
        current_run = prefect.context.get("flow_run_name")
        run_name = f"{current_run}-{flow_view.name}" if current_run else None

        # Now we submit the workflow
        logger.info(f"Creating flow run for {flow_view.name!r}...")
        client = Client()
        flow_run_id = client.create_flow_run(
            flow_id=flow_view.flow_id,
            parameters=parameters_serialized,
            context=context,
            labels=labels,
            run_name=run_name,
            run_config=run_config,
            scheduled_start_time=scheduled_start_time,
        )

        # we log the website url to the flow for the user
        run_url = client.get_cloud_url("flow-run", flow_run_id, as_user=False)
        logger.info(f"Created flow run: {run_url}")

        # return the flow_run_id so it can be used to track this flow run
        return flow_run_id

    def _wait_for_flow_run_prefect(
        self,
        flow_run_id,
        stream_states,
        stream_logs,
    ):
        """
        This method is a direct fork of...
            from prefect.tasks.prefect.flow_run import wait_for_flow_run

        It does exactly the same thing without any changes.
        """

        flow_run = FlowRunView.from_flow_run_id(flow_run_id)

        for log in watch_flow_run(
            flow_run_id,
            stream_states=stream_states,
            stream_logs=stream_logs,
        ):
            message = f"Flow {flow_run.name!r}: {log.message}"
            prefect.context.logger.log(log.level, message)

        # Return the final view of the flow run
        return flow_run.get_latest()

    @staticmethod
    def _serialize_parameters(parameters):
        # Because many flows allow object-type inputs (such as structure object),
        # we need to serialize these inputs before scheduling them with prefect
        # cloud. To do this, I only check for two potential methods:
        #   as_dict
        #   to_dict
        # These were chosen based on common pymatgen methods, but I may change
        # this in the future. As another alternative, I could also cloudpickle
        # input objects when they are not JSON serializable.

        # OPTIMIZE: Prefect current tries to JSON serialize within their
        # client.create_flow_run method. In the future, we may want to move
        # this functionality there.

        parameters_serialized = {}
        for parameter_key, parameter_value in parameters.items():

            try:
                json.dumps(parameter_value)
            except TypeError:
                if hasattr(parameter_value, "as_dict"):
                    parameter_value = parameter_value.as_dict()
                elif hasattr(parameter_value, "to_dict"):
                    parameter_value = parameter_value.as_dict()
                else:
                    parameter_value = cloudpickle.dumps(parameter_value)

            parameters_serialized[parameter_key] = parameter_value

        return parameters_serialized
