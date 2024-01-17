# -*- coding: utf-8 -*-

import inspect
import json
import logging
import re
import uuid
from functools import wraps
from pathlib import Path

import cloudpickle
import toml
import yaml
from django.utils import timezone

import simmate
from simmate.configuration import settings
from simmate.database.base_data_types import Calculation
from simmate.engine.execution import SimmateExecutor, WorkItem
from simmate.utilities import (
    copy_directory,
    copy_files_from_directory,
    get_directory,
    make_archive,
)


class DummyState:
    """
    This class is meant to emulate Prefect States. By wrapping a result into
    State, we enable higher-level features that depend on a call to
    `state.result()`.

    This class should not be used directly as it is automatically applied with
    the `Workflow.run` method
    """

    def __init__(self, result):
        self._result = result

    def result(self):
        return self._result

    @staticmethod
    def is_completed():
        return True


class Workflow:
    """
    An abstract base class for all Simmate workflows.
    """

    version: str = simmate.__version__
    """
    Version number for this flow. Defaults to the Simmate version 
    (e.g. "0.7.0").
    """

    description_doc_short: str = None
    """
    A quick description for this workflow. This will be shown in the website UI
    in the list-view of all different workflow presets.
    """

    use_database: bool = True
    """
    Whether to use Simmate database features or not.
    
    This includes calling the `_register_calculation` and 
    `_update_database_with_results` methods attached to this workflow.
    
    `_register_calculation` will save a database entry before the workflow
    starts. This is useful to keep track of workflows that have been
    submitted/started but haven't finished yet.
    
    `_update_database_with_results` saves the output of the `workup` method
    to the database entry -- and this the same entry that was created by 
    `_register_calculation`.
    """

    _parameter_methods: list[str] = ["run_config", "_run_full"]
    """
    List of methods that allow unique input parameters. This helps track where
    `**kwargs` are passed and let's us gather the inputs in one place.
    """

    exlcude_from_archives: list[str] = []
    """
    List of filenames that should be deleted when compressing the output files
    to a zip file (i.e. when compress_output=True). Any file name is searched
    for recursively in all subdirectories and removed.
    
    For example, VASP calculations remove all POTCAR files from archives.
    """

    # -------------------------------------------------------------------------
    # Helper attributes and methods for workflows that have prerequisites and/or
    # required files from previous calculations
    # -------------------------------------------------------------------------

    @classmethod
    @property
    def has_prerequisite(cls) -> bool:
        """
        Whether there is a prerequisite workflow for this one to work.

        If set to True, this is probably not a workflow the user will call
        directly (but instead they should call one set in `parent_workflows`).
        By default, this is set using `use_previous_directory` which
        gives False.
        """
        return bool(cls.use_previous_directory)

    parent_workflows: list[str] = []
    """
    Gives a list of recommeneded higher-level "parent" workflows that users 
    might prefer. These parent workflows will include this one AND extra steps.
    
    This should always be set if the workflow has `use_previous_directory` 
    set to True (or to filenames). These cases imply the workflow must have a
    parent workflow that runs the prerequisite steps and connects the result
    to this one.
    
    NOTE: This property has no effect on the actual workflow! It only helps
    improve error and help messages for users, so ommitting this is fine.
    """

    use_previous_directory: bool | list[str] = False
    """
    Whether this calculation requires a directory of files as an input.
    This also means there is a prerequisite workflow for this one to work, so
    setting this will also update the `has_prerquisite` property.
    
    When set to True, the entire previous directory will be copied to the new
    folder. Alternatively, this can be set to a list of filenames that will
    be selectively copied over from the previous directory to the new one.
    
    For example, Bader analysis requires the charge density file of a DFT 
    calculation, so a Bader workflow might set...
    `use_previous_directory=["CHGCAR"]`
    
    Workflows that have this set to True or a list of filenames MUST provide
    either 
    1. a database object from a previous calculation as a primary input
    2. `previous_directory` parameter
    
    Option 2 is not preferred because the source of your input files is then
    ambiguous. Meanwhile, Option 1 sets `source` automatically for you AND
    keeps track of old calculation files. This is important for tracking the
    history of a calculation and reproducing its results.
    
    NOTE: if this attribute is set, make sure you set parent_workflows too in
    order to give users helpful error messages.
    """

    # TODO: add `primary_input` as a class attribute that users can set! Right
    # now I just check from a list of potential inputs (see below)
    # primary_input: str = None

    # -------------------------------------------------------------------------
    # Core methods that handle how and what a workflow run does
    # and how it is submitted
    # -------------------------------------------------------------------------

    @classmethod
    def run(cls, **kwargs) -> DummyState:
        """
        The highest-level method to run a workflow. This includes calling
        `run_config` and all of the extra steps involved (such as registering
        a calculation to the database and creating the working directory).

        For advanced users, we recommend reading through the `_run_full` method
        to see the full workflow logic.
        """
        # Note: this is a separate method and wrapper around run_full because
        # we want to allow Prefect executor to overwrite this method.
        result = cls._run_full(**kwargs)
        state = DummyState(result)
        return state

    @classmethod
    def _run_full(
        cls,
        run_id: str = None,
        directory: Path | str = None,
        compress_output: bool = False,
        source: dict = None,
        **kwargs,
    ):
        """

        The full logic for a workflow run. This deserialize input parameters,
        register the calculation to the database, call the defined
        `run_config` command, and save results to the database.

        This method should not be called directly. Use the `run` method instead,
        which will properly convert to a `Prefect` workflow (if necessary) and
        return a State-like object.

        #### Parameters

        - `run_id`:
            A unique id that is assigned to the workflow run. If an ID was not
            provided, a randomly-generated id from
            [UUID4](https://docs.python.org/3/library/uuid.html#uuid.uuid4)
            is used. We recommend leaving this at default.

         - `directory`:
             The directory to run everything in. This is passed to the ulitities
             function simmate.ulitities.get_directory, which generates a
             unique foldername if not provided. This will be converted into
             a `pathlib.Path` object.

        - `compress_output`:
            Whether to compress the directory to a zip file at the end of the
            task run. After compression, it will also delete the directory.
            The default is False.

        - `source`: (EXPERIMENTAL FEATURE)
            The source is JSON-like information that indicates where the
            input for this calculation came from, which could be a number
            of things including (another calculation, a simple comment, etc.).
            This is useful if you want to label results in your database.

        """
        # This method is isolated only because we want to wrap it as a prefect
        # workflow in some cases.
        logging.info(f"Starting '{cls.name_full}'")
        kwargs_cleaned = cls._load_input_and_register(
            run_id=run_id,
            directory=directory,
            compress_output=compress_output,
            source=source,
            started_at=timezone.now(),
            **kwargs,
        )

        # Finally run the core part of the workflow. This should return a
        # dictionary object if we have "use_database=True", but can be
        # any python object if "use_database=False"
        results = cls.run_config(**kwargs_cleaned)

        # save the result to the database
        if cls.use_database:
            # make sure the workflow is returning a dictionary that be used
            # to update the database columns. None is also allowed as it
            # represents an empty dictionary
            if not isinstance(results, dict) and results != None:
                raise Exception(
                    "When using a database table, your `run_config` method must "
                    "return a dictionary object. The dictionary is used to "
                    "update columns in your table entry and is therefore a "
                    "required format. If you do not want to save to the database "
                    "(and avoid this message), set `use_database=False`"
                )
            logging.info("Saving to database and writing outputs")

            database_entry = cls._update_database_with_results(
                results=results if results != None else {},
                directory=kwargs_cleaned["directory"],
                run_id=kwargs_cleaned["run_id"],
                finished_at=timezone.now(),
            )

        # if requested, compresses the directory to a zip file and then removes
        # the directory.
        if compress_output:
            logging.info("Compressing result to a ZIP file.")
            make_archive(
                directory=kwargs_cleaned["directory"],
                files_to_exclude=cls.exlcude_from_archives,
            )

        # If we made it this far, we successfully completed the workflow run
        logging.info(f"Completed '{cls.name_full}'")

        # If we are using the database, then we return the database object.
        # Otherwise, we want to return the original result from run_config
        return database_entry if cls.use_database else results

    @classmethod
    def run_cloud(
        cls,
        tags: list[str] = [],
        **kwargs,
    ):
        """
        Submits the workflow run to cloud database to be ran by a worker.

        #### Parameters

        - `return_state`:
            Whether to return a State-like object or just the run_id. Defaults
            to true, which returns a State.

        - `tags`:
            A list of flags/labels/tags that the workflow run should be scheduled
            with. This helps with limiting which workers are allow to pickup
            and run the workflow. Defaults to the `tags` property of the
            workflow.
        """

        logging.info(f"Submitting new run of `{cls.name_full}` to cloud")

        # To help with tracking the flow in cloud, we load all of the inputs up
        # front. This will include creating a run_id for us.
        #
        # If we are submitting using a filename, we don't want to
        # submit to a cluster and have the job fail because it doesn't have
        # access to the file. We therefore go through the full load_input process
        kwargs_cleaned = cls._load_input_and_register(
            setup_directory=False,
            write_metadata=False,
            **kwargs,
        )

        # Some backends can't pickle input parameters, so we need to serialize
        # them before submission to the queue.
        parameters_serialized = cls._serialize_parameters(**kwargs_cleaned)

        # If tags were not provided, we add some default ones. Note, however,
        # that SQLite3 limits the default tag to just "simmate". The parameter
        # docs for `tags` explains this bug with SQLite
        if not tags:
            tags = cls.tags if settings.database_backend != "sqlite3" else ["simmate"]

        state = SimmateExecutor.submit(
            cls._run_full,  # should this be the run method...?
            tags=tags,
            **parameters_serialized,
        )

        logging.info(f"Successfully submitted (workitem_id={state.pk})")

        return state

    @classmethod
    def run_config(cls, **kwargs) -> any:
        """
        The workflow method, which can be overwritten when inheriting from this
        class. This can be either a `staticmethod` or `classmethod`.
        """
        raise NotImplementedError(
            "When creating a custom workflow, make sure you set a run_config method!"
        )

    # -------------------------------------------------------------------------
    # Methods for running/submitting workflows from input files (e.g. YAML/TOML)
    # -------------------------------------------------------------------------

    @classmethod
    def run_from_file(cls, filename: Path) -> DummyState:
        """
        Runs a workflow locally where parameters are loaded from a yaml or toml file
        """
        workflow, parameters = cls._load_settings_file(filename)
        state = workflow.run(**parameters)
        return state

    @classmethod
    def run_cloud_from_file(cls, filename: Path):
        """
        Submits a workflow to cloud for remote running where parameters are loaded
        from a yaml or toml file
        """
        workflow, parameters = cls._load_settings_file(filename)
        state = workflow.run_cloud(**parameters)
        return state

    @classmethod
    def _load_settings_file(cls, filename: Path):  # -> tuple[Workflow, dict]
        filename = Path(filename)

        # Load the settings to a dictionary using whichever format is given
        with filename.open() as file:
            if filename.suffix == ".yaml":
                parameters = yaml.full_load(file)
            elif filename.suffix == ".toml":
                parameters = toml.load(file)
            # elif filename.suffix == "json":  TODO consider allowing json
            #     parameters = json.load(file)
            else:
                raise Exception(
                    "Unknown input file format provided. Please make sure your "
                    "filename ends in either `.yaml` or `.toml`"
                )

        # If a workflow name is given, then we are actually calling this method
        # from the base workflow class -- and need to grab the proper workflow
        # object.
        if "workflow_name" in parameters.keys():
            # we are loading an external workflow, which will depend on this base
            # class. We need a local import to prevent circular-import bug.
            from simmate.workflows.utilities import get_workflow

            workflow = get_workflow(
                # we pop the workflow name so that it is also removed from the
                # rest of kwargs
                workflow_name=parameters.pop("workflow_name"),
            )
            return workflow, parameters

        # Otherwise we should be calling the proper workflow subclass already
        # and just return the workflow class itself.
        else:
            return cls, parameters

    # -------------------------------------------------------------------------
    # Methods that interact with the Executor class in order to see what
    # has been submitted to cloud.
    # -------------------------------------------------------------------------

    @classmethod
    @property
    def nflows_submitted(cls) -> int:
        """
        Queries the Simmate database to see how many workflows are in a
        running or pending state.
        """
        return WorkItem.objects.filter(
            status__in=["P", "R"],
            tags=cls.tags,
        ).count()

    # -------------------------------------------------------------------------
    # Methods that help with accessing the database and saving results
    # -------------------------------------------------------------------------

    @classmethod
    @property
    def database_table(cls) -> Calculation:
        """
        The database table where calculation information (such as the run_id)
        is stored. The table should use `simmate.database.base_data_types.Calculation`
        as one of its mix-ins.
        """
        # OPTIMIZE: a mapping dictionary or some standardized way to name
        # database tables would simplify this.

        flow_type = cls.name_type
        flow_preset = cls.name_preset

        if flow_type == "relaxation":
            from simmate.database.base_data_types import Relaxation

            return Relaxation
        elif flow_type == "static-energy":
            from simmate.database.base_data_types import StaticEnergy

            return StaticEnergy
        elif flow_type == "electronic-structure":
            if "band-structure" in flow_preset:
                from simmate.database.base_data_types import BandStructureCalc

                return BandStructureCalc
            elif "density-of-states" in flow_preset:
                from simmate.database.base_data_types import DensityofStatesCalc

                return DensityofStatesCalc
        elif flow_type == "population-analysis":
            from simmate.database.base_data_types import PopulationAnalysis

            return PopulationAnalysis
        elif flow_type == "dynamics":
            from simmate.database.base_data_types import Dynamics

            return Dynamics
        elif flow_type == "diffusion":
            if "from-images" in flow_preset or "single-path" in flow_preset:
                from simmate.database.base_data_types import MigrationHop

                return MigrationHop
            elif "all-paths" in flow_preset:
                from simmate.database.base_data_types import DiffusionAnalysis

                return DiffusionAnalysis

        raise NotImplementedError(
            "Unable to detect proper database table. Are you sure your workflow "
            "should be using a table? If not, set `use_database=False` on your "
            "workflow as shown in the 'basic' example workflow from the guides."
        )

    @classmethod
    @property
    def all_results(cls):  # -> SearchResults
        """
        Filters results from the database table down to the results from this
        workflow (i.e. matching workflow_name)
        """
        return cls.database_table.objects.filter(workflow_name=cls.name_full).all()

    @classmethod
    def _update_database_with_results(
        cls,
        results: dict,
        run_id: str,
        directory: Path,
        finished_at: timezone.datetime,
    ) -> Calculation:
        """
        Take the output of the `run_config` and any extra information and
        saves it to the database.

        An output summary is also written to file for quick viewing.
        """

        # load the calculation entry for this workflow run. This should already
        # exist thanks to the load_input_and_register task.
        calculation = cls.database_table.from_run_context(
            run_id=run_id,
            workflow_name=cls.name_full,
            workflow_version=cls.version,
            finished_at=finished_at,
        )

        # Now update the calculation entry with our results. Typically, all of this
        # is handled by the calculation table's "update_from" methods, but in
        # rare cares, we may want to attach an update method directly to the
        # workflow class. I can only imagine this is used when...
        #   (1) workflow attributes are important during the update
        #   (2) when several workflows share a table and need to isolate
        #       their workup method (e.g. the MigrationHop table for NEB)
        if hasattr(cls, "update_database_from_results"):
            # The attribute can also be set to false to disable updates
            if cls.update_database_from_results:
                cls.update_database_from_results(
                    calculation=calculation,
                    results=results,
                    directory=directory,
                )
        # Otherwise we hand this off to the database object
        else:
            calculation.update_from_results(
                results=results,
                directory=directory,
            )

        # write the output summary to file
        calculation.write_output_summary(directory)
        # TODO: consider making this optional to improve speedup

        return calculation

    @classmethod
    def load_completed_calc(cls, directory: Path):
        # TODO: maybe load the yaml file to get extra kwargs, run_id, etc.
        return cls.database_table.from_directory(directory)

    # -------------------------------------------------------------------------
    # Properties that enforce the naming convention for workflows
    # -------------------------------------------------------------------------

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
    def name_type(cls) -> str:
        """
        Name of the Project this workflow is associated with. This is the first
        portion of the flow name (e.g. "static-energy")
        """
        return cls.name_full.split(".")[0]

    @classmethod
    @property
    def name_app(cls) -> str:
        """
        Name of the app this workflow is associated with. This is the second
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

    @classmethod
    @property
    def tags(cls) -> list[str]:
        """
        Lists of tags to submit a the workflow with when using run_cloud.
        """
        return [
            "simmate",
            cls.name_type,
            cls.name_app,
            cls.name_full,
        ]

    # -------------------------------------------------------------------------
    # Properties/method that set website UI documentation and help users
    # explore input options and settings used.
    # -------------------------------------------------------------------------

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
        return cls.__doc__ or "No description provided"

    @classmethod
    @property
    def parameter_names(cls) -> list[str]:
        """
        Gives a list of all the parameter names for this workflow.
        """
        # Iterate through and grab the parameters for the core methods. We also
        # sort parameters alphabetically for consistent results.
        parameters = []
        for method in cls._parameter_methods:
            sig = inspect.signature(getattr(cls, method))
            for parameter in list(sig.parameters):
                if parameter not in parameters and parameter != "kwargs":
                    parameters += [parameter]
        parameters.sort()
        return parameters

    @classmethod
    @property
    def parameter_names_required(cls) -> list[str]:
        """
        Gives a list of all the required parameter names for this workflow.
        """
        parameters = []
        for method in cls._parameter_methods:
            sig = inspect.signature(getattr(cls, method))
            for parameter, val in sig.parameters.items():
                if (
                    parameter not in parameters
                    and parameter not in ["directory", "kwargs"]
                    and val.default == val.empty
                ):
                    parameters += [parameter]
        parameters.sort()
        return parameters

    @classmethod
    def show_parameters(cls):
        """
        Prints a list of all the parameter names for this workflow.
        """
        # use yaml to make the printout pretty (no quotes and separate lines)
        print("REQUIRED PARAMETERS")
        print("--------------------")
        print(yaml.dump(cls.parameter_names_required))

        print("OPTIONAL PARAMETERS (+ their defaults):")
        print("---------------------------------------")
        as_list = [{k: v} for k, v in cls.parameter_defaults.items()]
        print(yaml.dump(as_list))
        print("*** 'null' indicates the parameter is set with advanced logic\n")

    @classmethod
    @property
    def parameter_defaults(cls):
        """
        Inspect the run_config and other methods to see what the default
        value for an input parameter is.
        """
        defaults = {}
        for method in cls._parameter_methods:
            sig = inspect.signature(getattr(cls, method))
            for parameter_name in sig.parameters.keys():
                if parameter_name in cls.parameter_names:
                    value = sig.parameters[parameter_name]
                    if value.default == value.empty:
                        continue  # dont save if the value is none
                    defaults.update({parameter_name: value.default})

        # For a series of parameters, we want their default values to be loaded
        # from class attributes if they are not set. To do this, we first check
        # if the parameter is set in our kwargs dictionary and check if the
        # value is set to "None". If it is, then we change to the value set as
        # the class attribute.
        for parameter_name in cls.parameter_names:
            if hasattr(cls, parameter_name):
                defaults[parameter_name] = getattr(cls, parameter_name)

        return defaults

    @classmethod
    def get_config(cls):
        """
        Grabs the overall settings from the class in order to let users briefly
        look at key parameters.

        Using this method is scripts is not recommended.
        """
        return dict(
            use_database=cls.use_database,
            name_full=cls.name_full,
            parameter_names=cls.parameter_names,
            parameter_names_required=cls.parameter_names_required,
        )

    @classmethod
    def show_config(cls):
        """
        Takes the result of get_config and prints it in a yaml format that is
        easier to read.
        """
        config = cls.get_config()
        print(yaml.dump(config))

    # -------------------------------------------------------------------------
    # Properties/method that configure registration of workflow runs and the
    # parameters each is called with.
    # -------------------------------------------------------------------------

    @classmethod
    def _load_input_and_register(
        cls,
        setup_directory: bool = True,
        write_metadata: bool = True,
        **parameters: any,
    ) -> dict:
        """
        How the input was submitted as a parameter depends on if we are submitting
        to Prefect Cloud, running the flow locally, or even continuing from a
        previous calculation.  Here, we use a task to convert the input to a toolkit
        object and (if requested) provide the directory as well.

        For example, a common input parameter for workflows is "structure", which
        can be provided a number of ways:
            - a filename
            - a json string
            - a dictionary pointing to a database entry
            - a toolkit Structure object
            - etc...
        Even though all of these inputs are accepted, `workflow.run_config` always
        expects python objects, so this utility converts the input to a toolkit
        Structure object.


        If `setup_directory` is True, this is also where `use_previous_directory`
        is applied and used.

        `**parameters` includes all parameters and anything extra that you want saved
        to simmate_metadata.yaml AND submitted to executor
        """

        # OPTIMIZE: consider splitting this task into load_structure, load_directory,
        # and register_calc so that our flow_visualize looks cleaner

        # OPTIMIZE: Customized workflows cause a lot of special handling in this task
        # so it may be worth isolating these into a separate task.

        # ---------------------------------------------------------------------

        # STEP 1: clean parameters & grab "primary input"

        parameters_cleaned = cls._deserialize_parameters(**parameters)

        # Primary input is the paramater that can be a database object from
        # an older run -- such as a database structure object. This allows
        # us to dynamically set source and also determine where old directories
        # can be pulled from.
        # Currently I just set a priority of possible parameters that can be
        # the primary input. I go through each one at a time until I find one
        # that was provided -- then I exit with that parameter's value.
        primary_input = None
        for primary_input_key in [
            "structure",
            "molecule",
            "migration_hop",
            "supercell_start",
        ]:
            if primary_input_key in parameters_cleaned.keys():
                # note we grab the deserialized input
                primary_input = parameters_cleaned.get(primary_input_key, None)
                break

        # ---------------------------------------------------------------------

        # STEP 2: Load the source of the input object

        source = parameters.get("source", None)

        # detect primary input source if there is one
        if primary_input and hasattr(primary_input, "source") and primary_input.source:
            primary_source = primary_input.source
        else:
            primary_source = None

        # User-given source is our first check
        if source and not primary_source:
            source_cleaned = source
        # Check if we have a primary input loaded from a past calculation and
        # default to that as the backup source.
        elif primary_source and not source:
            source_cleaned = primary_source
        # stop users from overriding the "correct" source which is the primary one
        elif primary_source and source:
            raise Exception(
                "You provided both a source and a primary source input for this workflow. "
                "For calculations that use database inputs (e.g. from MatProj or a past "
                "calculation), you should NOT set the `source` parameter as it is "
                "determined automatically. You gave...\n"
                f"source={source}\nbut autodetection found...\nsource={primary_source}"
            )
        # otherwise no source was given
        else:
            source_cleaned = None

        # before setting the source, we also need it to be json-seralized
        # for the database
        source_cleaned = cls._serialize_parameters(source=source_cleaned)["source"]

        # SPECIAL CASE for customized flows
        if "workflow_base" not in parameters_cleaned:
            parameters_cleaned["source"] = source_cleaned
        else:
            parameters_cleaned["input_parameters"]["source"] = source_cleaned

        # ---------------------------------------------------------------------

        # STEP 3: Load the directory (and copy over from an old directory if necessary)

        if setup_directory:
            # Start by creating a new directory or grabbing the one given. We create
            # this directory immediately (rather than just passing the name to the
            # S3Task). We do this because NestedWorkflows often use a parent directory
            # to organize results.
            directory = parameters.get("directory", None)
            directory_cleaned = get_directory(directory)

            # if this workflow requires input files from a previous directory
            # and/or calcuation, then we configure that here as well
            if cls.use_previous_directory:
                # see if the user provided a previous_directory input option
                previous_directory = parameters.get("previous_directory", None)

                # alternatively, the past directory should be stored on the
                # primary input object. This is the preferred method, but the
                # previous_directory input parameter takes priority
                if (
                    not previous_directory
                    and primary_input.database_object
                    and hasattr(primary_input.database_object, "directory")
                ):
                    previous_directory = Path(primary_input.database_object.directory)

                # at least one of two inputs above needs to be set
                if not previous_directory:
                    raise Exception(
                        "This workflow requires either an input from a past calculation "
                        "or a previous_directory set to run but neither was given."
                    )

                # If "True" was given, then we copy over all files except
                # simmate ones (we have no need for the summaries or error archives)
                if cls.use_previous_directory == True:
                    copy_directory(
                        directory_old=previous_directory,
                        directory_new=directory_cleaned,
                        ignore_simmate_files=True,
                    )
                # alternatively users can give a list of filenames to copy
                elif isinstance(cls.use_previous_directory, list):
                    copy_files_from_directory(
                        files_to_copy=cls.use_previous_directory,
                        directory_old=previous_directory,
                        directory_new=directory_cleaned,
                    )
                else:
                    raise Exception(
                        f"Unknown input for previous_directory: {previous_directory}"
                        f"({type(cls.use_previous_directory)})"
                    )

                parameters_cleaned["previous_directory"] = Path(previous_directory)

            # SPECIAL CASE for customized flows
            if "workflow_base" not in parameters_cleaned:
                parameters_cleaned["directory"] = directory_cleaned
            else:
                parameters_cleaned["input_parameters"]["directory"] = directory_cleaned

        # ---------------------------------------------------------------------

        # STEP 4: Register the calculation so the user can follow along in the UI
        # and also see which structures/runs have been submitted aready.

        parameters_cleaned["run_id"] = (
            parameters_cleaned.get("run_id", None) or cls._get_new_run_id()
        )

        if cls.use_database:
            cls._register_calculation(**parameters_cleaned)

        # ---------------------------------------------------------------------

        # STEP 5: Write metadata file for user reference

        if write_metadata:
            # convert back to json format. We convert back rather than use the original
            # to ensure the input data is all present. For example, we want to store
            # structure data instead of a filename in the metadata.
            # SPECIAL CASE: "if ..." used to catch customized workflows
            parameters_serialized = (
                cls._serialize_parameters(**parameters_cleaned)
                if "workflow_base" not in parameters_cleaned
                else parameters
            )

            # We want to write a file summarizing the inputs used for this
            # workflow run. This allows future users to reproduce the results if
            # desired -- and it also allows us to load old results into a database.
            input_summary = dict(
                _WORKFLOW_NAME_=cls.name_full,
                _WORKFLOW_VERSION_=cls.version,
                **parameters_serialized,
            )

            # now write the summary to file in the same directory as the calc.
            # check the directory and see how many other "simmate_metadata*.yaml" files
            # already exist. Our new file will be based off of this. Simply,
            # if the biggest number is 04 --> then we will write a file named
            # simmate_metadata__05.yaml to keep the count going.
            count = (
                len(
                    [
                        f
                        for f in directory_cleaned.iterdir()
                        if f.name.startswith("simmate_metadata_")
                    ]
                )
                + 1
            )
            count_str = str(count).zfill(2)
            input_summary_file = (
                directory_cleaned / f"simmate_metadata_{count_str}.yaml"
            )
            with input_summary_file.open("w") as file:
                content = yaml.dump(input_summary)
                file.write(content)

        # ---------------------------------------------------------------------

        # Finally we just want to return the dictionary of cleaned parameters
        # to be used by the workflow
        return parameters_cleaned

    @staticmethod
    def _get_new_run_id():
        """
        Generates a random id to use as a workflow run id.

        This is called automatically within `_load_input_and_register`
        """
        # This is a separate method in order to allow the prefect executor to
        # overwrite this method.
        unique_id = str(uuid.uuid4())
        return unique_id

    @classmethod
    @property
    def _parameters_to_register(cls) -> list[str]:
        """
        A list of input parameters that should be used to register the calculation.
        """

        # run is always used to register but is never an input parameter
        parameters_to_register = []
        # workflow_name is also used to register but this implemented within
        # the _register_calculation method

        table_columns = cls.database_table.get_column_names()

        # as an extra, we need to check for relations and add also check for
        # "_id" added on to the name in case we want to register the new entry
        # with this relation. An example of this is "diffusion_analysis_id"
        # which is a related object and column.
        for field in cls.database_table._meta.get_fields():
            if field.is_relation:  # and isinstance(ForeignKey)
                # we append BOTH but only one should be found during registration
                table_columns.append(field.name)
                table_columns.append(f"{field.name}_id")

        for parameter in cls.parameter_names:
            if parameter in table_columns:
                parameters_to_register.append(parameter)

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
        `run_prefect_cloud` method and `load_input_and_register` task.
        """

        # grab the registration kwargs from the parameters provided and then
        # convert them to a python object format for the database method
        register_kwargs = {
            key: kwargs.get(key, None) for key in cls._parameters_to_register
        }
        register_kwargs_cleaned = cls._deserialize_parameters(
            add_defaults=False, **register_kwargs
        )

        # as an extra, the start time is always registered for ALL calc if given
        if "started_at" in kwargs.keys():
            register_kwargs_cleaned["started_at"] = kwargs["started_at"]

        # SPECIAL CASE: The exception to the above is with SOURCE, which needs
        # to be in a JSON-serialized form for the database
        if "source" in register_kwargs_cleaned:
            register_kwargs_cleaned["source"] = cls._serialize_parameters(
                source=kwargs.get("source", None)
            )["source"]
            # !!! This is a hacky bug fix that needs refactored

        # SPECIAL CASE: for customized workflows we need to convert the inputs
        # back to json before saving to the database.
        if "workflow_base" in register_kwargs_cleaned:
            parameters_serialized = cls._serialize_parameters(**register_kwargs_cleaned)
            calculation = cls.database_table.from_run_context(
                workflow_name=cls.name_full,
                workflow_version=cls.version,
                **parameters_serialized,
            )
        else:
            # load/create the calculation for this workflow run
            calculation = cls.database_table.from_run_context(
                workflow_name=cls.name_full,
                workflow_version=cls.version,
                **register_kwargs_cleaned,
            )

        return calculation

    # -------------------------------------------------------------------------
    # Methods that hanlde serialization and deserialization of input parameters.
    # -------------------------------------------------------------------------

    @classmethod
    def _update_with_defaults(cls, parameter_dict: dict) -> dict:
        """
        updates a dictoinary default input parameters if they were provided
        """
        for parameter_name, default_value in cls.parameter_defaults.items():
            if (
                parameter_dict.get(parameter_name, None) is None
                and default_value is not None
            ):
                parameter_dict[parameter_name] = default_value

    @classmethod
    def _serialize_parameters(cls, **parameters) -> dict:
        """
        Converts input parameters to json-sealiziable objects that Prefect can
        use.

        This method should not be called directly as it is used within the
        run_prefect_cloud() method.
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
                # Special cases
                if parameter_key == "directory":
                    # convert Path to str
                    parameter_value = str(parameter_value)
                elif parameter_key == "source" and isinstance(parameter_value, dict):
                    # recursive call to this function
                    parameter_value = cls._serialize_parameters(**parameter_value)
                elif parameter_key == "composition":
                    # convert Composition to str
                    parameter_value = str(parameter_value)

                # preferred serializiation
                elif hasattr(parameter_value, "as_dict"):
                    parameter_value = parameter_value.as_dict()
                elif hasattr(parameter_value, "to_dict"):
                    parameter_value = parameter_value.to_dict()
                elif hasattr(parameter_value, "to_binary"):
                    parameter_value = parameter_value.to_binary()

                # workflow_base and input_parameters are special cases that
                # may require a refactor (for customized workflows)
                elif parameter_key == "workflow_base":
                    parameter_value = parameter_value.name_full
                elif parameter_key == "input_parameters":
                    # recursive call to this function
                    parameter_value = cls._serialize_parameters(**parameter_value)

                else:
                    parameter_value = cloudpickle.dumps(parameter_value)
            parameters_serialized[parameter_key] = parameter_value
        return parameters_serialized

    @classmethod
    def _deserialize_parameters(
        cls,
        add_defaults: bool = True,
        **parameters,
    ) -> dict:
        """
        converts all parameters to appropriate python objects
        """

        from simmate.toolkit import Composition, Structure
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

            # Make sure we have a workflow object
            parameters_cleaned["workflow_base"] = (
                get_workflow(parameters["workflow_base"])
                if isinstance(parameters["workflow_base"], str)
                else parameters["workflow_base"]
            )
            # Make a recursive call for the input parameters
            parameters_cleaned["input_parameters"] = Workflow._deserialize_parameters(
                **parameters["input_parameters"]
            )
            return parameters_cleaned
        #######

        # We populate this dictionary using the default input parameters if
        # they were provided.
        if add_defaults:
            cls._update_with_defaults(parameters_cleaned)

        # The remaining checks look to intialize input to toolkit objects using
        # the from_dynamic methods.
        # OPTIMIZE: if I have proper typing and parameter itrospection, I could
        # potentially grab the from_dynamic method on the fly -- rather than
        # doing these repeated steps here.
        parameter_mappings = {
            "structure": Structure,
            "composition": Composition,
            "migration_hop": MigrationHop,
            "migration_images": MigrationImages,
            "supercell_start": Structure,
            "supercell_end": Structure,
        }
        # Add extra parameter mappings from internal code
        try:
            from simmate_corteva.toolkit import Molecule

            parameter_mappings.update(
                {
                    "molecule": Molecule,
                    "molecules": Molecule,
                }
            )
        except:
            pass  # just move on if there's no module present

        for parameter, target_class in parameter_mappings.items():
            if parameter in parameters.keys():
                parameter_orig = parameters.get(parameter, None)
                parameters_cleaned[parameter] = target_class.from_dynamic(
                    parameter_orig
                )

        # directory and source are two extra parameters that cant be used in the
        # mapping above because they don't have a `from_dynamic` method.
        # Note these also pull from 'parameters_cleaned' as they might have been
        # populated during registration.

        if parameters.get("directory", None):
            parameters_cleaned["directory"] = Path(parameters_cleaned["directory"])

        if parameters.get("source", None):
            # !!! are there other types I should account for? Maybe I should just
            # make this a recursive call to catch everything?
            if isinstance(parameters_cleaned["source"], dict) and parameters_cleaned[
                "source"
            ].get("directory", None):
                parameters_cleaned["source"]["directory"] = Path(
                    parameters_cleaned["directory"]
                )

        return parameters_cleaned


def workflow(
    original_function: callable = None,
    app_name: str = "Basic",
    type_name: str = "Toolkit",
    use_database: bool = False,
):
    """
    A decorator that converts a function into a workflow class.

    ## Example use:

    ``` python
    @workflow
    def example(name, **kwargs):
        print(f"Hello {name}!")
        return 12345
    ```
    """

    def decorator(original_function):
        @wraps(original_function)
        def wrapper(*args, **kwargs):
            # Preset name example: 'example_fxn' --> 'ExampleFxn'
            # code copied from https://stackoverflow.com/questions/4303492/
            preset_name = "".join(
                x.capitalize() or "_" for x in original_function.__name__.split("_")
            )

            # dynamically create the new Workflow subclass.
            NewClass = type(
                f"{app_name}__{type_name}__{preset_name}",
                tuple([Workflow]),
                {
                    "run_config": staticmethod(original_function),
                    "use_database": use_database,
                },
            )

            return NewClass

        # BUG-FIX: normally we don't call the wrapper here, but I do this
        # to make sure the function immediately returns our new class.
        return wrapper()

    # Check if the decorator is used with or without arguments
    if original_function is None:
        return decorator
    else:
        return decorator(original_function)
