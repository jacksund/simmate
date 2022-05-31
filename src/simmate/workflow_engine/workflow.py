# -*- coding: utf-8 -*-

import json
import cloudpickle
import yaml
from typing import List, Any, Union

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

from simmate.toolkit import Structure
from simmate.toolkit.diffusion import MigrationHop
from simmate.database.base_data_types import DatabaseTable, Calculation
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
    The name of the project in the  that this workflow is associated with. This 
    attribute is mainly just for organizing workflows in the Prefect Cloud interface.
    """

    s3task: S3Task = None
    """
    The supervised-staged-shell task (or S3Task) that this workflow uses to run.
    For understanding what the calculation does and the settings it uses, users
    should start here. You can also use a workflows `s3task.run` to run the workflow
    without storing results in the database.
    """

    calculation_table: Calculation = None
    """
    The database table where calculation information (such as the prefect_flow_run_id)
    is stored. Note, for NestedWorkflows, this table will not be the same as the
    result table! The table should use 
    `simmate.database.base_data_types.Calculation`
    """

    result_table: DatabaseTable = None
    """
    The database table where all calculation results are stored. In many cases,
    this is the same table as `calculation_table` -- the exception is
    for NestedWorkflows, where the result table may point to a specific
    sub-workflow's table for results. An example of this is the relaxation/staged
    workflow, which is made up of a series of relaxations -- and the result 
    table points to the final relaxation in this series. The table should use 
    `simmate.database.base_data_types.DatabaseTable`
    """

    description_doc_short: str = None
    """
    A quick description for this workflow. This will be shown in the website UI
    in the list-view of all different workflow presets.
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

    def run(self, **kwargs: Any) -> Union["prefect.engine.state.State", None]:
        # Simply deserializes inputs before calling the normal workflow.run
        # method. We leave the docstring empty for inheritance.
        kwargs_cleaned = self._deserialize_parameters(**kwargs)
        return super().run(**kwargs_cleaned)

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

        # Deserialize and then Serialize all of the parameters so they can be properly submitted
        parameters_deserialized = self._deserialize_parameters(**kwargs)
        parameters_serialized = self._serialize_parameters(**parameters_deserialized)
        # NOTE: This may seem odd to deserialize right before serializing in the
        # next line, but this is done to ensure parameters that accept file names
        # are submitted properly. i.e -- We don't want to submit to a cluster and
        # have the job fail because it doesn't have access to the file. Having
        # these lines back-to-back ensures we submit with all necessary data.

        # Now we submit the workflow
        logger.info(f"Creating flow run for {self.name}...") if logger else None
        client = Client()
        flow_run_id = client.create_flow_run(
            flow_id=flow_view.flow_id,
            parameters=parameters_serialized,
            labels=labels,
        )

        # we log the website url to the flow for the user
        run_url = client.get_cloud_url("flow-run", flow_run_id, as_user=False)
        logger.info(f"Created flow run: {run_url}") if logger else None

        # -----------------------------------
        # This part is unique to Simmate. Because we often want to save some info
        # to our database even before the calculation starts/finishes, we do that
        # here. An example is storing the structure and prefect id that we just
        # submitted.
        # BUG: Will there be a race condition here? What if the workflow finishes
        # and tries writing to the databse before this is done?
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
        # just skip this step. Otherwise save/load the calculation to our table
        if self.calculation_table:
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

        for log in flow_run_module.watch_flow_run(flow_run_id):
            message = f"Flow {flow_run.name}: {log.message}"
            prefect.context.logger.log(log.level, message)
        # Return the final view of the flow run
        return flow_run.get_latest()

    @staticmethod
    def _deserialize_parameters(**parameters) -> dict:
        """
        Converts input parameters to proper python objects. This handles the
        variety of formats accepted by Simmate.

        For example, a common input parameter for workflows is "structure", which
        can be provided a number of ways:
            - a filename
            - a json string
            - a dictionary pointing to a database entry
            - a toolkit Structure object
            - etc...
        Even though all of these inputs are accepted, `workflow.run` always expects
        python objects, so this utility converts the input to a toolkit Structure
        object.

        This method should not be called directly as it is used within higher-level
        methods such as run() and run_cloud().
        """

        # we don't want to pass arguments like command=None or structure=None if the
        # user didn't provide this input parameter. Instead, we want the workflow to
        # use its own default value. To do this, we first check if the parameter
        # is set in our kwargs dictionary and making sure the value is NOT None.
        # If it is None, then we remove it from our final list of kwargs. This
        # is only done for command, directory, and structure inputs -- as these
        # are the three that are typically assumed to be present (see the CLI).

        if not parameters.get("command", None):
            parameters.pop("command", None)

        if not parameters.get("directory", None):
            parameters.pop("directory", None)

        structure = parameters.get("structure", None)
        if structure:
            parameters["structure"] = Structure.from_dynamic(structure)
        else:
            parameters.pop("structure", None)

        if "structures" in parameters.keys():
            structure_filenames = parameters["structures"].split(";")
            parameters["structures"] = [
                Structure.from_dynamic(file) for file in structure_filenames
            ]

        if "migration_hop" in parameters.keys():
            migration_hop = MigrationHop.from_dynamic(parameters["migration_hop"])
            parameters["migration_hop"] = migration_hop

        if "supercell_start" in parameters.keys():
            parameters["supercell_start"] = Structure.from_dynamic(
                parameters["supercell_start"]
            )

        if "supercell_end" in parameters.keys():
            parameters["supercell_end"] = Structure.from_dynamic(
                parameters["supercell_end"]
            )

        # lastly, for customized workflows, we need to completely change the format
        # that we provide the parameters. Customized workflows expect parameters
        # broken into a dictionary of
        #   {"workflow_base": ..., "input_parameters":..., "updated_settings": ...}
        # The
        if "workflow_base" in parameters.keys():

            # This is a non-modular import that can cause issues and slower
            # run times. We therefore import lazily.
            from simmate.workflows.utilities import get_workflow

            parameters["workflow_base"] = get_workflow(parameters["workflow_base"])
            parameters["input_parameters"] = {}
            parameters["updated_settings"] = {}

            for key, update_values in list(parameters.items()):
                if key in ["workflow_base", "input_parameters", "updated_settings"]:
                    continue
                elif not key.startswith("custom__"):
                    parameters["input_parameters"][key] = parameters.pop(key)
                # Otherwise remove the prefix and add it to the custom settings.
                else:
                    key_cleaned = key.removeprefix("custom__")
                    parameters["updated_settings"][key_cleaned] = parameters.pop(key)

        return parameters

    @staticmethod
    def _serialize_parameters(**parameters) -> dict:
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
                    parameter_value = parameter_value.to_dict()
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
