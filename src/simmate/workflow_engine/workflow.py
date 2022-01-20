# -*- coding: utf-8 -*-

import json
import cloudpickle

# note: extra modules are imported from prefect for convenience imports elsewhere
import prefect
from prefect import Client
from prefect import Flow as PrefectFlow, Parameter, task, Task
from prefect.storage import Module as ModuleStorage
from prefect.utilities.graphql import with_args

from prefect.backend.flow_run import FlowRunView, FlowView, watch_flow_run

from typing import List


class Workflow(PrefectFlow):
    """
    This class behaves exactly like a normal Prefect workflow, where we add some
    common utilities and pre-submit tasks. For example, there is the `run_cloud`
    methods, which us to register a calculation along with submitting a workflow
    to the cloud.

    To learn how to use this class, see [prefect.core.flow.Flow](https://docs.prefect.io/api/latest/core/flow.html#flow-2)
    """

    result_task = None
    """
    In many ETL workflows, we may also want the result of the some terminating
    task directly. This would save us from having to go find the result in
    the database. So by setting `result_task`, we are able get access a specific task's
    result -- directly as a python object(s). This is optional.
    """

    def run_cloud(
        self,
        labels: List[str] = [],
        wait_for_run: bool = True,
        **kwargs,
    ) -> str:
        """
        This schedules the workflow to run remotely on Prefect Cloud.

        Parameters
        ----------

        - `labels`:
            a list of labels to schedule the workflow with

        - `wait_for_run`:
            whether to wait for the workflow to finish. If False, the workflow
            will simply be submitted and then exit. The default is True.

        - `**kwargs`:
            all options that are normally passed to the workflow.run() method

        Returns
        -------

        - The flow run id that was used in prefect cloud.


        Usage
        -----

        Make sure you have Prefect properly configured and have registered your
        workflow with the backend.

        Note that this method can be viewed as a fork of:
            - from prefect.tasks.prefect.flow_run import create_flow_run
        It can also be viewed as a more convenient way to call to client.create_flow_run.
        I don't accept any other client.create_flow_run() inputs besides 'labels'.
        This may change in the future if I need to set flow run names or schedules.
        """

        # Grab the logger as we will print useful information below
        logger = prefect.context.logger

        # Grab the Flow's ID from Prefect Cloud
        logger.debug("Looking up flow metadata...")
        flow_view = FlowView.from_flow_name(
            self.name,
            project_name=self.project_name,
        )

        # Serialize all of the parameters so they can be properly submitted
        parameters_serialized = self._serialize_parameters(kwargs)

        # Now we submit the workflow
        logger.info(f"Creating flow run for {self.name}...")
        client = Client()
        flow_run_id = client.create_flow_run(
            flow_id=flow_view.flow_id,
            parameters=parameters_serialized,
            labels=labels,
        )

        # we log the website url to the flow for the user
        run_url = client.get_cloud_url("flow-run", flow_run_id, as_user=False)
        logger.info(f"Created flow run: {run_url}")

        # -----------------------------------
        # This part is unique to Simmate. Because we often want to save some info
        # to our database even before the calculation starts/finishes, we do that
        # here. An example is storing the structure and prefect id that we just
        # submitted.
        # BUG: Will there be a race condition here? What if the workflow finishes
        # and tries writing to the databse before this is done?
        # BUG: When registering a calc, will I ever need anything besides id
        # and structure? What else should I add here?
        register_kwargs = {
            key: kwargs[key] for key in kwargs if key in self.register_kwargs
        }
        calc = self._register_calculation(
            flow_run_id,
            **register_kwargs,
        )  # !!! should I return the calc to the user?
        # -----------------------------------

        # if we want to wait until the job is complete, we do that here
        if wait_for_run:
            flow_run_view = self.wait_for_flow_run(flow_run_id)
            # return flow_run_view # !!! Should I return this instead?
        # return the flow_run_id for the user
        return flow_run_id

    def _register_calculation(self, flow_run_id: str, **kwargs):
        """
        If the workflow is linked to a calculation table in the Simmate database,
        this adds the flow run to the Simmate database.

        This method should not be called directly as it is used within the
        run_cloud() method.
        """
        # If there's no calculation database table in Simmate for this workflow,
        # just skip this step.
        if not hasattr(self, "calculation_table"):
            return
        # otherwise save/load the calculation to our table
        calculation = self.calculation_table.from_prefect_id(
            id=flow_run_id,
            **kwargs,
        )
        return calculation

    def wait_for_flow_run(self, flow_run_id: str):
        """
        Waits for a given flow run to complete

        This method is a direct fork of...
            from prefect.tasks.prefect.flow_run import wait_for_flow_run

        It does exactly the same thing where I just assume I want to stream logs.
        """

        flow_run = FlowRunView.from_flow_run_id(flow_run_id)

        for log in watch_flow_run(flow_run_id):
            message = f"Flow {flow_run.name}: {log.message}"
            prefect.context.logger.log(log.level, message)
        # Return the final view of the flow run
        return flow_run.get_latest()

    @staticmethod
    def _serialize_parameters(parameters: dict) -> dict:
        """
        Converts input parameters to json-sealiziable objects that Prefect can
        use.

        This method should not be called directly as it is used within the
        run_cloud() method.
        """
        # Because many flows allow object-type inputs (such as structure object),
        # we need to serialize these inputs before scheduling them with prefect
        # cloud. To do this, I only check for two potential methods:
        #     as_dict
        #     to_dict
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

    @property
    def nflows_submitted(self) -> int:
        """
        Queries Prefect to see how many workflows are in a running or submitted
        state. It will return a count (integer).

        Note, your workflow must be registered with Prefect for this to work.
        """
        query = {
            "query": {
                with_args(
                    "flow_run_aggregate",
                    {
                        "where": {
                            "flow": {"name": {"_eq": self.name}},
                            "state": {"_in": ["Running", "Scheduled"]},
                        },
                    },
                ): {"aggregate": {"count"}}
            }
        }
        client = Client()
        result = client.graphql(query)
        return result["data"]["flow_run_aggregate"]["aggregate"]["count"]

    def to_workflow_task(self):
        """
        Converts a prefect workflow to a prefect task (aka a "workflow task")

        See the documentation in workflow_engine.tasks.workflow_task for more.
        """
        from simmate.workflow_engine import WorkflowTask

        return WorkflowTask(workflow=self)


# TODO: This is an example query where I grab all ids. This may be useful in the
# future.
# query = {
#     "query": {
#         with_args(
#             "flow_run",
#             {
#                 "where": {
#                     "flow": {"name": {"_eq": "MIT Relaxation"}},
#                     "state": {"_in": ["Completed", "Scheduled"]},
#                 },
#             },
#         ): ["id"]
#     }
# }
