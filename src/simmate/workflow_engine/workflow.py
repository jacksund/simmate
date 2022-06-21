# -*- coding: utf-8 -*-

import json
import cloudpickle
import yaml
from typing import List

# note: extra modules are imported from prefect for convenience imports elsewhere
import prefect
from prefect import Client
from prefect import Flow as PrefectFlow, Parameter, task, Task
from prefect.storage import Module as ModuleStorage
from prefect.utilities.graphql import with_args
from prefect.backend import FlowRunView, FlowView

# This import below is used to grab `watch_flow_run`, but we don't grab it directly
# in order to support "mocking" this function in unit tests
from prefect.backend import flow_run as flow_run_module

from simmate.database.base_data_types import Calculation
from simmate.workflow_engine import S3Task


class Workflow(PrefectFlow):
    """
    This class behaves exactly like a normal Prefect workflow, where we add some
    common utilities and pre-submit tasks. For example, there is the `run_cloud`
    method, which allows us to register a calculation to a database table before
    we submit the workflow to Prefect Cloud.

    To learn how to use this class, see
    [prefect.core.flow.Flow](https://docs.prefect.io/api/latest/core/flow.html#flow-2)
    """

    result_task: Task = None
    """
    In many ETL workflows, we may also want the result of the some terminating
    task directly. This would save us from having to go find the result in
    the database. So by setting `result_task`, we are able get access a specific task's
    result -- directly as a python object(s). This is optional.
    """

    project_name: str = None
    """
    The name of the project in Prefect Cloud that this workflow is associated with. This 
    attribute is mainly just for organizing workflows in the web interface.
    """

    s3task: S3Task = None
    """
    The supervised-staged-shell task (or S3Task) that this workflow uses to run.
    For understanding what the calculation does and the settings it uses, users
    should start here. You can also use a workflows `s3task.run` to run the workflow
    without storing results in the database.
    """

    database_table: Calculation = None
    """
    The database table where calculation information (such as the prefect_flow_run_id)
    is stored. The table should use `simmate.database.base_data_types.Calculation`
    
    In many cases, this table will contain all of the results you need. However,
    pay special attention to NestedWorkflows, where your results are often tied
    to a final task.
    """

    description_doc_short: str = None
    """
    A quick description for this workflow. This will be shown in the website UI
    in the list-view of all different workflow presets.
    """

    register_kwargs: List[str] = []
    """
    (experimental feature)
    A list of input parameters that should be used to register the calculation.
    """

    @property
    def type(self) -> str:
        """
        Gives the workflow type of this workflow. For example the workflow named
        'static-energy/matproj' would have the type `static-energy`.
        """
        return self.name.split("/")[0]

    @property
    def name_short(self) -> str:
        """
        Gives the present name of the workflow. For example the workflow named
        'static-energy/matproj' would have the shortname `matproj`
        """
        return self.name.split("/")[-1]

    # BUG: naming this `description` causes issues.
    # See https://github.com/PrefectHQ/prefect/issues/3911
    @property
    def description_doc(self) -> str:
        """
        This simply returns the documentation string of this workflow -- so this
        is the same as `__doc__`. This attribute is only defined for beginners
        to python and for use in django templates for the website interface.
        """
        return self.__doc__

    @property
    def parameter_names(self):
        """
        Prints a list of all the parameter names for this workflow.
        """
        # Iterate through and grab the columns. Note we don't use get_column_names
        # here because we are attaching relation data as well. We also
        # sort them alphabetically for consistent results.
        parameter_names = [parameter.name for parameter in self.parameters()]
        parameter_names.sort()
        return parameter_names

    def show_parameters(self):
        """
        Prints a list of all the parameter names for this workflow.
        """
        # use yaml to make the printout pretty (no quotes and separate lines)
        print(yaml.dump(self.parameter_names))

    def run_cloud(
        self,
        labels: List[str] = [],
        wait_for_run: bool = True,
        **kwargs,
    ) -> str:
        """
        This schedules the workflow to run remotely on Prefect Cloud.

        #### Parameters

        - `labels`:
            a list of labels to schedule the workflow with

        - `wait_for_run`:
            whether to wait for the workflow to finish. If False, the workflow
            will simply be submitted and then exit. The default is True.

        - `**kwargs`:
            all options that are normally passed to the workflow.run() method

        #### Returns

        - The flow run id that was used in prefect cloud.


        #### Usage

        Make sure you have Prefect properly configured and have registered your
        workflow with the backend.

        Note that this method can be viewed as a fork of:
            - from prefect.tasks.prefect.flow_run import create_flow_run
        It can also be viewed as a more convenient way to call to client.create_flow_run.
        I don't accept any other client.create_flow_run() inputs besides 'labels'.
        This may change in the future if I need to set flow run names or schedules.
        """

        # Grab the logger as we will print useful information below.
        # In some cases, there is no logger present, so we just set logger=None.
        # This possibility is why we use `if logger else None` statements below.
        logger = getattr(prefect.context, "logger", None)

        # Grab the Flow's ID from Prefect Cloud
        logger.debug("Looking up flow metadata...") if logger else None
        flow_view = FlowView.from_flow_name(
            self.name,
            project_name=self.project_name,
        )

        # Prefect does not properly deserialize objects that have
        # as as_dict or to_dict method, so we use a custom method to do that here
        parameters_serialized = self._serialize_parameters(**kwargs)
        # BUG: What if we are submitting using a filename? We don't want to
        # submit to a cluster and have the job fail because it doesn't have
        # access to the file. One solution could be to deserialize right before
        # serializing in the next line in order to ensure parameters that
        # accept file names are submitted with all necessary data.

        # Now we submit the workflow
        logger.info(f"Creating flow run for {self.name}...") if logger else None
        client = Client()
        flow_run_id = client.create_flow_run(
            flow_id=flow_view.flow_id,
            parameters=parameters_serialized,
            labels=labels,
        )

        # we log the website url to the flow for the user
        run_url = client.get_cloud_url("flow-run", flow_run_id)
        logger.info(f"Created flow run: {run_url}") if logger else None

        # -----------------------------------
        # This part is unique to Simmate. Because we often want to save some info
        # to our database even before the calculation starts/finishes, we do that
        # here. An example is storing the structure and prefect id that we just
        # submitted.
        # BUG: Will there be a race condition here? What if the workflow finishes
        # and tries writing to the databse before this is done?
        parameters_cleaned = self._deserialize_parameters(**kwargs)
        self._register_calculation(flow_run_id, parameters_cleaned)
        # -----------------------------------

        # if we want to wait until the job is complete, we do that here
        if wait_for_run:
            flow_run_view = self.wait_for_flow_run(flow_run_id)
            # return flow_run_view # !!! Should I return this instead?

        # return the flow_run_id for the user
        return flow_run_id

    def wait_for_flow_run(self, flow_run_id: str):
        """
        Waits for a given flow run to complete

        This method is a direct fork of...
            from prefect.tasks.prefect.flow_run import wait_for_flow_run

        It does exactly the same thing where I just assume I want to stream logs.
        """

        flow_run = FlowRunView.from_flow_run_id(flow_run_id)

        for log in flow_run_module.watch_flow_run(flow_run_id):
            message = f"Flow {flow_run.name}: {log.message}"
            prefect.context.logger.log(log.level, message)

        # Return the final view of the flow run
        return flow_run.get_latest()

    def _register_calculation(self, prefect_flow_run_id, parameters):
        """
        If the workflow is linked to a calculation table in the Simmate database,
        this adds the flow run to the database.

        Parameters passed should be deserialized and cleaned.

        This method should not be called directly as it is used within the
        `run_cloud` method and `load_input_and_register` task.
        """

        # grab the registration kwargs from the parameters provided
        register_kwargs = {
            key: parameters.get(key, None) for key in self.register_kwargs
        }

        # SPECIAL CASE: for customized workflows we need to convert the inputs
        # back to json before saving to the database.
        if "workflow_base" in parameters:
            parameters_serialized = self._serialize_parameters(**parameters)
            calculation = self.database_table.from_prefect_id(
                id=prefect_flow_run_id,
                **parameters_serialized,
            )
        else:
            # load/create the calculation for this workflow run
            calculation = self.database_table.from_prefect_id(
                id=prefect_flow_run_id,
                **register_kwargs,
            )

    @staticmethod
    def _serialize_parameters(**parameters) -> dict:
        """
        Converts input parameters to json-sealiziable objects that Prefect can
        use.

        This method should not be called directly as it is used within the
        run_cloud() method.
        """
        # TODO: consider moving this into prefect's core code as a contribution.

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
                    parameter_value = parameter_value.to_dict()

                # workflow_base and input_parameters are special cases that
                # may require a refactor (for customized workflows)
                elif parameter_key == "workflow_base":
                    parameter_value = parameter_value.name
                elif parameter_key == "input_parameters":
                    # recursive call to this function
                    parameter_value = Workflow._serialize_parameters(**parameter_value)

                else:
                    parameter_value = cloudpickle.dumps(parameter_value)
            parameters_serialized[parameter_key] = parameter_value
        return parameters_serialized

    @staticmethod
    def _deserialize_parameters(**parameters) -> dict:
        """
        converts all parameters to appropriate python objects
        """

        # we don't want to pass arguments like command=None or structure=None if the
        # user didn't provide this input parameter. Instead, we want the workflow to
        # use its own default value. To do this, we first check if the parameter
        # is set in our kwargs dictionary and making sure the value is NOT None.
        # If it is None, then we remove it from our final list of kwargs. This
        # is only done for command, directory, and structure inputs -- as these
        # are the three that are typically assumed to be present (see the CLI).

        from simmate.toolkit import Structure
        from simmate.toolkit.diffusion import MigrationHop, MigrationImages

        parameters_cleaned = parameters.copy()

        #######
        # SPECIAL CASE: customized workflows have their parameters stored under
        # "input_parameters" instead of the base dict
        # THIS INVOLVES A RECURSIVE CALL TO THIS SAME METHOD
        if "workflow_base" in parameters.keys():
            # This is a non-modular import that can cause issues and slower
            # run times. We therefore import lazily.
            from simmate.workflows.utilities import get_workflow

            parameters_cleaned["workflow_base"] = get_workflow(
                parameters["workflow_base"]
            )
            parameters_cleaned["input_parameters"] = Workflow._deserialize_parameters(
                **parameters["input_parameters"]
            )
            return parameters_cleaned
        #######

        if not parameters.get("command", None):
            parameters_cleaned.pop("command", None)

        if not parameters.get("directory", None):
            parameters_cleaned.pop("directory", None)

        structure = parameters.get("structure", None)
        if structure:
            parameters_cleaned["structure"] = Structure.from_dynamic(structure)
        else:
            parameters_cleaned.pop("structure", None)

        if "structures" in parameters.keys():
            structure_filenames = parameters["structures"].split(";")
            parameters_cleaned["structures"] = [
                Structure.from_dynamic(file) for file in structure_filenames
            ]

        if "migration_hop" in parameters.keys():
            migration_hop = MigrationHop.from_dynamic(parameters["migration_hop"])
            parameters_cleaned["migration_hop"] = migration_hop

        if "migration_images" in parameters.keys():
            migration_images = MigrationImages.from_dynamic(
                parameters["migration_images"]
            )
            parameters_cleaned["migration_images"] = migration_images

        if "supercell_start" in parameters.keys():
            parameters_cleaned["supercell_start"] = Structure.from_dynamic(
                parameters["supercell_start"]
            )

        if "supercell_end" in parameters.keys():
            parameters_cleaned["supercell_end"] = Structure.from_dynamic(
                parameters["supercell_end"]
            )

        return parameters_cleaned

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

    # @classmethod
    # def get_all_ids_in_state(cls, states=["Completed", "Scheduled"]):
    #     # TODO: This is an example query where I grab all ids. This may be useful in the
    #     # future.
    #     query = {
    #         "query": {
    #             with_args(
    #                 "flow_run",
    #                 {
    #                     "where": {
    #                         "flow": {"name": {"_eq": cls.name}},
    #                         "state": {"_in": states},
    #                     },
    #                 },
    #             ): ["id"]
    #         }
    #     }
