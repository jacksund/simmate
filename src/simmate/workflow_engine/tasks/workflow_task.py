# -*- coding: utf-8 -*-

"""
Many times in Material Science, a workflow is made up of other smaller workflows.
For example, calculations for bandstructure first involve a structure relaxation
followed by a static energy calculation -- before the bandstructure is even
calculated.

For this reason, we need a way to call these workflows as if they were a task.
Prefect has a module prefect.tasks.prefect.flow_run which is close to this
idea -- but this module requires you to be using Prefect Cloud and have all
of the flows registered. We need to account for running flows locally too!
Therefore, we had to make this custom task here -- where it decided whether
we call the workflow.run_cloud or workflow.run method.
"""

from prefect import Task
from prefect.utilities.tasks import defaults_from_attrs

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
#     # file. We check for this in the file ".simmate/extra_applications".
#     # For windows, this would be something like...
#     #   C:\Users\exampleuser\.simmate\executor.yaml
#     SIMMATE_DIRECTORY = os.path.join(Path.home(), ".simmate")
#     EXECUTOR_YAML = os.path.join(SIMMATE_DIRECTORY, "executor.yaml")
#     if os.path.exists(EXECUTOR_YAML):
#         with open(EXECUTOR_YAML) as file:
#             EXECUTOR_TYPE = yaml.full_load(file)["EXECUTOR_TYPE"]
#     else:
#         EXECUTOR_TYPE = "local"
#     return EXECUTOR_TYPE


class WorkflowTask(Task):
    def __init__(
        self,
        # The full workflow to run.
        workflow,
        # How the workflow should be scheduled and ran. The options are either
        # local or prefect (i.e. prefect cloud).
        executor_type="local",  # get_default_executor_type(), # BUG
        # If Prefect is used to schedule the workflow, then this indicates
        # whether we should wait for the flow to finish or not. Also what
        # labels should be attached to the flow
        wait_for_run=True,
        labels=[],
        # If Prefect is used to schedule the workflow, we also may want to
        # To support other Prefect input options. To see all the options, visit...
        # https://docs.prefect.io/api/latest/core/task.html
        # We want to pass the logs from the workflow task up!
        log_stdout=True,
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
        self.labels = labels

        # now inherit the parent Prefect Task class
        # Note we name this task after our attached workflow
        super().__init__(
            name=f"{self.workflow.name}-WorkflowTask",
            log_stdout=log_stdout,
            **kwargs,
        )

    @defaults_from_attrs(
        "executor_type",
        "wait_for_run",
        "labels",
    )
    def run(
        self,
        executor_type=None,
        wait_for_run=None,
        labels=None,
        **parameters,
    ):
        # The kwargs here are any parameter you would normally pass into the
        # workflow.run() method.

        # If we want this ran locally, we can run the workflow directly. We
        # also make sure the workflow is successful -- otherwise we want to
        # raise an error so that this task is flagged as failed
        if executor_type == "local":
            state = self.workflow.run(**parameters)
            if state.is_failed():
                # Grab the very first task error and we raise that.
                # TODO: what if we want to raise all task errors (excluding those
                # like "TriggerFailed")?
                # OPTIMIZE: would the log_stdout=True task option be the better
                # way to forward information? See here:
                #   https://docs.prefect.io/core/concepts/logging.html#logging-stdout
                for task_state in state.result.values():
                    if task_state.is_failed():
                        error = task_state.result
                        break  # exits for-loop
                # we want the error raised so that the task fails
                raise error
            return state

        # If we are using prefect, we assume that the flow has been registered
        # and simply submit it from here.
        elif executor_type == "prefect":
            # Now create the flow run in the prefect cloud
            flow_run_id = self.workflow.run_cloud(
                labels,
                wait_for_run,
                **parameters,
            )
            if wait_for_run:
                raise Exception("wait_for_run not implemented for cloud yet")
            return flow_run_id
