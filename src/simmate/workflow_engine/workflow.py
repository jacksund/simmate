# -*- coding: utf-8 -*-

import json
import cloudpickle
import yaml
import re
from typing import List

from prefect.tasks import task  # present only for convience imports elsewhere
from prefect.flows import Flow
from prefect.states import State
from prefect.context import FlowRunContext

# from prefect.client import get_client

import simmate
from simmate.toolkit import Structure
from simmate.database.base_data_types import Calculation
from simmate.workflow_engine import S3Task


class Workflow:
    """
    This class behaves exactly like a normal Prefect workflow, where we add some
    common utilities and pre-submit tasks. For example, there is the `run_cloud`
    method, which allows us to register a calculation to a database table before
    we submit the workflow to Prefect Cloud.

    To learn how to use this class, see
    [prefect.core.flow.Flow](https://docs.prefect.io/api/latest/core/flow.html#flow-2)
    """

    # TODO: set storage attribute to module

    # TODO: inherit doc from s3task
    # by default we just copy the docstring of the S3task to the workflow
    # workflow.__doc__ = s3task.__doc__

    version: str = simmate.__version__
    """
    Version number for this flow. Defaults to the Simmate version 
    (e.g. "0.7.0").
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

    @classmethod
    def run_config(
        cls,
        structure: Structure,
        command: str = None,
        source: dict = None,
        directory: str = None,
        copy_previous_directory: bool = False,
    ):
        """
        The workflow method, which can be overwritten when inheriting from this
        class. This can be either a staticmethod or classmethod.

        #### The default run method

        There is a default run method implemented that is for S3Tasks.

        Builds a workflow from a S3Task and it's corresponding database table.

        Very often with Simmate's S3Tasks, the workflow for a single S3Task is
        the same. The workflow is typically made of three tasks:

        1. loading the input parameters and registering the calculation
        2. running the calculation (what this S3Task does on its own)
        3. saving the calculation results

        Task 1 and 3 always use the same functions, where we just need to tell
        it which database table we are registering/saving to.

        Because of this common recipe for workflows, we use this method to make
        the workflow for us.
        """
        # local import to prevent circular import error
        from simmate.workflow_engine.common_tasks import (
            load_input_and_register,
            save_result,
        )

        # make sure the workflow is configured properly first
        if not cls.s3task:
            raise NotImplementedError(
                "Please either set the s3task attribute or write a custom run method!"
            )

        parameters_cleaned = load_input_and_register(
            structure=structure,
            command=command,
            source=source,
            directory=directory,
            copy_previous_directory=copy_previous_directory,
        ).result()

        result = cls.s3task.run(**parameters_cleaned).result()

        save_result(result)

        return result

    @classmethod
    def to_prefect_flow(cls) -> Flow:
        """
        Converts this workflow into a Prefect flow
        """
        # Instead of the @flow decorator, we build the flow instance directly
        flow = Flow(
            fn=cls.run_config,
            name=cls.name_full,
            version=cls.version,
            # Skip type checking because I don't have robust typing yet
            # e.g. Structure type inputs also accept inputs like a filename
            validate_parameters=False,
        )

        # as an extra, we set this attribute to the prefect flow instance, which
        # allows us to access the source Simmate Workflow easily with Prefect's
        # context managers.
        flow.simmate_workflow = cls

        return flow

    @classmethod
    def run(cls, **kwargs) -> State:
        """
        A convience method to run a workflow as a subflow in a prefect context.
        """
        subflow = cls.to_prefect_flow()
        state = subflow(**kwargs)

        # We don't want to block and wait because this might disable parallel
        # features of subflows. We therefore return the state and let the
        # user decide if/when to block.
        # result = state.result()

        return state

    @classmethod
    @property
    def name_full(cls) -> str:
        """
        Standardized name of the workflow. This converts the class name like so:
        `Static_Energy__VASP__Matproj` --> `static-energy.vasp.matproj`
        """
        if not len(cls.__name__.split("__")) == 3:
            raise Exception("Make sure you are following Simmate naming conventions!")

        # convert to dot format
        name = cls.__name__.replace("__", ".")

        # adds a hyphen between each capital letter
        # copied from https://stackoverflow.com/questions/199059/
        name = re.sub(r"(\w)([A-Z])", r"\1-\2", name)

        return name.lower()

    @classmethod
    @property
    def name_project(cls) -> str:
        """
        Name of the Project this workflow is associated with. This is the first
        portion of the flow name (e.g. "static-energy")
        """
        return cls.name_full.split(".")[0]

    @classmethod
    @property
    def name_calculator(cls) -> str:
        """
        Name of the calculator this workflow is associated with. This is the second
        portion of the flow name (e.g. "vasp")
        """
        return cls.name_full.split(".")[1]

    @classmethod
    @property
    def name_preset(cls) -> str:
        """
        Name of the settings/preset this workflow is associated with. This is the third
        portion of the flow name (e.g. "matproj" or "matproj-prebader")
        """
        return cls.name_full.split(".")[2]

    # BUG: naming this `description` causes issues.
    # See https://github.com/PrefectHQ/prefect/issues/3911
    @classmethod
    @property
    def description_doc(cls) -> str:
        """
        This simply returns the documentation string of this workflow -- so this
        is the same as `__doc__`. This attribute is only defined for beginners
        to python and for use in django templates for the website interface.
        """
        return cls.__doc__

    @classmethod
    @property
    def parameter_names(cls) -> List[str]:
        """
        Gives a list of all the parameter names for this workflow.
        """
        # Iterate through and grab the parameters for the run method. We also
        # sort them alphabetically for consistent results.
        parameter_names = list(cls.to_prefect_flow().parameters.properties.keys())
        parameter_names.sort()
        return parameter_names

    @classmethod
    def show_parameters(cls):
        """
        Prints a list of all the parameter names for this workflow.
        """
        # use yaml to make the printout pretty (no quotes and separate lines)
        print(yaml.dump(cls.parameter_names))

    @classmethod
    @property
    def parameters_to_register(cls) -> List[str]:
        """
        (experimental feature)
        A list of input parameters that should be used to register the calculation.
        """
        parameters_to_register = [
            "prefect_flow_run_id"
        ]  # run is always used to register but is never an input parameter

        table_columns = cls.database_table.get_column_names()

        for parameter in cls.parameter_names:
            if parameter in table_columns:
                parameters_to_register.append(parameter)

        # check special cases where input parameter doesn't match to a column name
        if "structure_string" in table_columns:
            parameters_to_register.append("structure")

        # put in alphabetical order for consistent results
        parameters_to_register.sort()

        return parameters_to_register

    @classmethod
    def _register_calculation(cls, **kwargs) -> Calculation:
        """
        If the workflow is linked to a calculation table in the Simmate database,
        this adds the flow run to the database.

        Parameters passed should be deserialized and cleaned.

        This method should not be called directly as it is used within the
        `run_cloud` method and `load_input_and_register` task.
        """

        # We first need to grab the database table where we want to register
        # the calculation run to. We can grab the table from either...
        #   1. the database_table attribute
        #   2. flow_context --> flow_name --> flow --> then grab its database_table

        # If this method is being called on the base Workflow class, that
        # means we are trying to register a calculation from within a flow
        # context -- where the context has information such as the workflow
        # we are using (and the database table linked to that workflow).
        if cls == Workflow:

            run_context = FlowRunContext.get()
            workflow = run_context.flow.simmate_workflow
            database_table = workflow.database_table

            # as an extra, add the prefect_flow_run_id the kwargs in case it
            # wasn't set already.
            if "prefect_flow_run_id" not in kwargs:
                kwargs["prefect_flow_run_id"] = str(run_context.flow_run.id)

        # Otherwise we should be using the subclass Workflow that has the
        # database_table property set.
        else:
            workflow = cls  # we have the workflow class already
            database_table = cls.database_table

        # Registration is only possible if a table is provided. Some
        # special-case workflows don't store calculation information bc the flow
        # is just a quick python analysis.
        if not database_table:
            print("No database table found. Skipping registration.")
            return

        # grab the registration kwargs from the parameters provided and then
        # convert them to a python object format for the database method
        register_kwargs = {
            key: kwargs.get(key, None) for key in workflow.parameters_to_register
        }
        register_kwargs_cleaned = cls._deserialize_parameters(**register_kwargs)

        # SPECIAL CASE: for customized workflows we need to convert the inputs
        # back to json before saving to the database.
        if "workflow_base" in register_kwargs_cleaned:
            parameters_serialized = cls._serialize_parameters(**register_kwargs_cleaned)
            prefect_flow_run_id = parameters_serialized.pop("prefect_flow_run_id", None)
            calculation = database_table.from_prefect_id(
                prefect_flow_run_id=prefect_flow_run_id,
                **parameters_serialized,
            )
        else:
            # load/create the calculation for this workflow run
            calculation = database_table.from_prefect_id(**register_kwargs_cleaned)

        return calculation

    @staticmethod
    def _serialize_parameters(**parameters) -> dict:
        """
        Converts input parameters to json-sealiziable objects that Prefect can
        use.

        This method should not be called directly as it is used within the
        run_cloud() method.
        """

        # TODO: consider moving this into prefect's core code as a contribution.
        # This alternatively might be a pydantic contribution

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

    # -------------------------------------------------------------------------
    #
    # All methods beyond this point require a Prefect server to be running
    # and Simmate to be connected to it.
    #
    # -------------------------------------------------------------------------

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
        raise NotImplementedError("Migrating to Prefect 2.0")

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
        self._register_calculation(prefect_flow_run_id=flow_run_id, **kwargs)
        # BUG: Will there be a race condition here? What if the workflow finishes
        # and tries writing to the databse before this is done?
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
        raise NotImplementedError("Migrating to Prefect 2.0")

        flow_run = FlowRunView.from_flow_run_id(flow_run_id)

        for log in flow_run_module.watch_flow_run(flow_run_id):
            message = f"Flow {flow_run.name}: {log.message}"
            prefect.context.logger.log(log.level, message)

        # Return the final view of the flow run
        return flow_run.get_latest()

    @property
    def nflows_submitted(self) -> int:
        """
        Queries Prefect to see how many workflows are in a running or submitted
        state. It will return a count (integer).

        Note, your workflow must be registered with Prefect for this to work.
        """
        raise NotImplementedError("Migrating to Prefect 2.0")

        # new api may look like...
        # async with get_client() as client:
        #     response = await client.read_flow_runs(flow_filter="...")
        # return response

        # OLD API...
        # query = {
        #     "query": {
        #         with_args(
        #             "flow_run_aggregate",
        #             {
        #                 "where": {
        #                     "flow": {"name": {"_eq": self.name}},
        #                     "state": {"_in": ["Running", "Scheduled"]},
        #                 },
        #             },
        #         ): {"aggregate": {"count"}}
        #     }
        # }
        # client = Client()
        # result = client.graphql(query)
        # return result["data"]["flow_run_aggregate"]["aggregate"]["count"]
