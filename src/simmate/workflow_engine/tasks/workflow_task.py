# -*- coding: utf-8 -*-

from prefect import Task
from prefect.utilities.tasks import defaults_from_attrs
from prefect.engine.state import TriggerFailed

from typing import List
from simmate.workflow_engine.workflow import Workflow

# BUG: prefect executor causes issues because there is no aysncio. Therefore the
# "waiting" step means a task will be holding onto two Dask workers. Because of this
# Prefect cloud has been disabled as an executor.
#
# import os
# from pathlib import Path
# import yaml
# def get_default_executor_type():
#     # rather than always specifying the executor type whenever this class is used,
#     # it's much more convenient to set the default value here based on a config
#     # file. We check for this in the file "simmate/extra_applications".
#     # For windows, this would be something like...
#     #   C:\Users\exampleuser\simmate\executor.yaml
#     SIMMATE_DIRECTORY = os.path.join(Path.home(), "simmate")
#     EXECUTOR_YAML = os.path.join(SIMMATE_DIRECTORY, "executor.yaml")
#     if os.path.exists(EXECUTOR_YAML):
#         with open(EXECUTOR_YAML) as file:
#             EXECUTOR_TYPE = yaml.full_load(file)["EXECUTOR_TYPE"]
#     else:
#         EXECUTOR_TYPE = "local"
#     return EXECUTOR_TYPE


class WorkflowTask(Task):
    """
    Many times in Material Science, a workflow is made up of other smaller workflows.
    For example, calculations for bandstructure first involve a structure relaxation
    followed by a static energy calculation -- before the bandstructure is even
    calculated.

    For this reason, we need a way to call these workflows as if they were a task.

    The easiest way to make your Workflow into a WorkflowTask is actually NOT
    calling this class. But instead using the to_workflow_task method:

    ``` python
    from simmate.workflows import example_workflow

    my_task = example_workflow.to_workflow_task()
    ```
    """

    # DEV NOTE:
    # Prefect has a module prefect.tasks.prefect.flow_run which is close to this
    # idea -- but this module requires you to be using Prefect Cloud and have all
    # of the flows registered. We need to account for running flows locally too!
    # Therefore, we had to make this custom task here -- where it decided whether
    # we call the workflow.run_cloud or workflow.run method.
    # Consider moving this functionality to Prefect down the line.

    def __init__(
        self,
        workflow: Workflow,
        return_result=True,
        executor_type: str = "local",  # get_default_executor_type(), # BUG
        wait_for_run: bool = True,
        labels: List[str] = [],
        log_stdout: bool = True,
        **kwargs,
    ):
        """
        Creates a Prefect task instance from a workflow and determines how it
        should be ran when task.run() is called.

        Parameters
        ----------
        - `workflow`:
            The full workflow to run.
        - `return_result`:
            If True, the task run will return the result of the task set as the
            worfklow.result_task attribute. If False, the workflow State is returned.
            The default is True.
        - `executor_type`:
            How the workflow should be scheduled and ran. The options are either
            local or prefect (i.e. prefect cloud). The default is "local".
        - `wait_for_run`:
            If Prefect is used to schedule the workflow, then this indicates
            whether we should wait for the flow to finish or not.
        - `labels`:
            If Prefect is used to schedule the workflow, then this indicates
            what labels should be attached to the flow
        - `log_stdout`:
            Whether to log anything printed by the workflow. The default is True.
        - `**kwargs`:
            All extra arguments supported by
            [prefect.core.task.Task](https://docs.prefect.io/api/latest/core/task.html).
        """

        # If Prefect is used to schedule the workflow, we also may want to
        # To support other Prefect input options. To see all the options, visit...
        # https://docs.prefect.io/api/latest/core/task.html
        # We want to pass the logs from the workflow task up!

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
        self.return_result = return_result
        self.executor_type = executor_type
        self.wait_for_run = wait_for_run
        self.labels = labels

        # BUG: so far I only support local execution
        if executor_type != "local":
            raise Exception("Only executor_type=local is supported right now.")

        # now inherit the parent Prefect Task class
        # Note we name this task after our attached workflow
        super().__init__(
            name=f"{self.workflow.name}-WorkflowTask",
            log_stdout=log_stdout,
            **kwargs,
        )

    @defaults_from_attrs(
        "executor_type",
        "return_result",
        "wait_for_run",
        "labels",
    )
    def run(
        self,
        executor_type: str = None,
        return_result: bool = None,
        wait_for_run: bool = None,
        labels: List[str] = None,
        **parameters,
    ):
        """


        Parameters
        ----------
        - `executor_type`:
            How the workflow should be scheduled and ran. The options are either
            local or prefect (i.e. prefect cloud).
        - `return_result`:
            If True, the task run will return the result of the task set as the
            worfklow.result_task attribute. If False, the workflow State is returned.
            The default is True.
        - `wait_for_run`:
            If Prefect is used to schedule the workflow, then this indicates
            whether we should wait for the flow to finish or not.
        - `labels`:
            If Prefect is used to schedule the workflow, then this indicates
            what labels should be attached to the flow
        - `**parameters`:
            All options to pass the workflow.run() method.

        Returns
        -------
        str
            The flow-run-id if submitted with prefect OR the prefect state if
            the workflow was ran locally

        """
        # The kwargs here are any parameter you would normally pass into the
        # workflow.run() method.

        # If we want this ran locally, we can run the workflow directly. We
        # also make sure the workflow is successful -- otherwise we want to
        # raise an error so that this task is flagged as failed
        if executor_type == "local":
            state = self.workflow.run(**parameters)
            if state.is_failed():
                # Grab the all task errors except for those that never ran
                # because the trigger failed.
                # OPTIMIZE: would the log_stdout=True task option be the better
                # way to forward information? See here:
                #   https://docs.prefect.io/core/concepts/logging.html#logging-stdout
                errors = []
                for task_state in state.result.values():
                    if task_state.is_failed() and not isinstance(
                        task_state, TriggerFailed
                    ):
                        error = task_state.result
                        errors.append(error)

                # TODO: how do you raise a list of errors?
                if len(errors) > 1:
                    raise Exception(
                        "More than one task failed in the workflow and Simmate does "
                        "not currently have a way to raise a list of errors."
                    )
                # otherwise we just have one failure
                else:
                    # we want the error raised so that the task fails
                    raise errors[0]
            # if we reached this point, the workflow was successful and we just return
            # the state as a normal task would

            # Workflows typically return a prefect State object, but when we run
            # workflows as a task, we often want to pass along extra information
            # beyond just some "state". So return_result is True, we return the
            # result of a specific task (determined by flow.result_task).
            if self.return_result and self.workflow.result_task:
                # The prefect api for this is ugly... nothing I can really do
                # about it: https://docs.prefect.io/core/concepts/results.html
                return state.result[self.workflow.result_task].result
            else:
                return state

        # If we are using prefect, we assume that the flow has been registered
        # and simply submit it from here.
        elif executor_type == "prefect":

            raise Exception

            # Now create the flow run in the prefect cloud
            flow_run_id = self.workflow.run_cloud(
                labels,
                wait_for_run,
                **parameters,
            )
            if wait_for_run:
                raise Exception("wait_for_run not implemented for cloud yet")
            return flow_run_id
