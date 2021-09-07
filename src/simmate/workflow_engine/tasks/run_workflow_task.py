# -*- coding: utf-8 -*-

# Many times in Material Science, a workflow is made up of other smaller workflows.
# For example, calculations for bandstructure first involve a structure relaxation
# followed by a static energy calculations -- before the band structure is even
# calculated.
#
# For this reason, we need a way to call these workflows as if they were a task.
# Prefect has a module prefect.tasks.prefect.flow_run which is close to this
# idea -- but this module requires you to be using Prefect Cloud and have all
# of the flows registered. We need to account for running flows locally too!
# Therefore, we had to make this custom task here.

from prefect.core.task import Task
from prefect.tasks.prefect.flow_run import create_flow_run, wait_for_flow_run


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
        self.executor = executor_type
        self.wait_for_run = wait_for_run

        # now inherit the parent Prefect Task class
        super().__init__(**kwargs)

    def run(self, **kwargs):
        # The kwargs here are any parameter you would normally pass into the
        # workflow.run() method.

        # If we want this ran locally, we can run the workflow directly. We
        # also make sure the workflow is successful -- otherwise we want to
        # raise an error so that this task is flagged as failed
        if self.executor_type == "local":
            status = self.workflow.run(**kwargs)
            assert status.is_successful()

        # If we are using prefect, we assume that the flow has been registered
        # and simply submit it from here.
        elif self.executor_type == "prefect":
            # Note: the .run() is because these are tasks runs and not just simple function calls.
            flow_run_id = create_flow_run.run(
                flow_name=self.workflow.name, 
                parameters=dict(**kwargs),
            )
            # if we want to wait until the job is complete, we do that and
            # also make sure that it completed successfully
            if self.wait_for_run:
                flow_run_view = create_flow_run.run(flow_run_id=flow_run_id)
                assert flow_run_view.state.is_successful()
