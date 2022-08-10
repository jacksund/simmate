# -*- coding: utf-8 -*-

"""
This module defines the base class for all workflows in Simmate. When learning 
how use workflows, make sure you have gone through our intro 
[tutorials](https://github.com/jacksund/simmate/tree/main/tutorials). You
can then read through these guides for more features.

It useful to know that our Worklfow class builds Prefect Flows under the 
hood, so having knowledge of Prefect can be useful in advanced cases. For 
advanced use or when building new features, we recommend going through the
prefect tutorials located
[here](https://orion-docs.prefect.io/tutorials/first-steps/).



# Using existing workflows


## Loading a workflow

To import a specific workflow, see the `simmate.workflows` module. For all the
example uses below, we will look at the `static-energy.vasp.matproj` workflow,
which we load with:
    
``` python
from simmate.workflows.all import StaticEnergy__Vasp__Matproj as workflow
```


## Viewing input parameters



## Running a workflow (local)

To run a workflow locally (i.e. directly on your current computer), you can
use the `run` method. This is returns a Prefect `State` object, which allows
you to check if the run completed successfully or not. Then final output of your
workflow run can be accessed using `state.result()`. You can read more about
`State` objects [here](https://orion-docs.prefect.io/concepts/states/), but as
a quick example:

``` python
state = workflow.run(
    structure="NaCl.cif", 
    command="mpirun -n 4 vasp_std > vasp.out",
)

if state.is_completed():  # optional check
    result = state.result()
```

Outside of python, you can also run workflows from the command line, using YAML 
files, or the website interface. These approaches are covered in the intro
tutorials.


## Running a workflow (cloud)

When you want to schedule a workflow to run elsewhere, you must first make sure
you have your computational resources configured. You can then run workflows
using the `run_cloud` method, which returns a Prefect flow run id.

``` python
run_id = workflow.run_cloud(
    structure="NaCl.cif", 
    command="mpirun -n 4 vasp_std > vasp.out",
)
```

## Accessing results

In addition to using `state.result()` as described above, you can also view
results database through the `database_table` attribute (if one is available).
This returns a Simmate database object for results of ALL runs of this workflow.
Guides for filtering and manulipating the data in this table is covered in
the `simmate.database` module guides. But as an example:

``` python
table = workflow.database_table

# pandas dataframe that you can view in Spyder
df = table.obects.to_dataframe()

# or grab a specific run result and convert to a toolkit object
entry = table.objects.get(run_id="example-123456")
structure = entry.to_toolkit()
```

<!--
TODO:
    - viewing parameter names
    - accessing results (database_table)
    - run_cloud and other cloud methods
    - different documentation levels (parameters, mini docstring, etc.)
    - finding the same workflow in the website UI (place this )
-->

# Creating new workflows

## Naming workflows (required)

Higher level features such as the website interface require that workflow
names follow a certain format. If you skip this step, your workflows
will fail and cause errors elsewhere.

First, we need to update the workflow name to match Simmate's naming
conventions, which includes:
    1.  The type of analysis the workflow is doing
    2.  The "calculator" (or program) that the workflow uses to run
    3.  A unique name to identify the settings used

Examples for each part would be:
    1. relaxation, static-energy, dynamics, ...
    2. vasp, abinit, qe, deepmd, ...
    3. jacks-test, matproj, quality00, ...

Together, an example workflow names would be:
    - `relaxation.vasp.jacks-test`
    - `static-energy.abinit.matproj`
    - `dynamics.qe.quality00`

When converting this to our workflow name in python, we need to replace
periods with 2 underscores each and convert our words to
[pascal case](https://khalilstemmler.com/blogs/camel-case-snake-case-pascal-case/).
For example, our workflow names become:
    - `Relaxation__Vasp__JacksTest`
    - `StaticEnergy__Abinit__Matproj`
    - `Dynamics__Qe__Quality00`

NOTE: Capitalization is very important here so make sure you double check
your workflow names.

Now let's test this out in python using a similar workflow name:
``` python
from simmate.workflow_engine import Workflow

class Example__Python__MyFavoriteSettings(Workflow):
    pass  # we will build the rest of workflow later

# These names can be long and unfriendly, so it can be nice to
# link them to a variable name for easier access.
my_workflow = Example__Python__MyFavoriteSettings

# Now check that our naming convention works as expected
assert my_workflow.name_full == "example.pure-python.my-favorite-settings"
assert my_workflow.name_type == "example"
assert my_workflow.name_calculator == "python"
assert my_workflow.name_preset == "my-favorite-settings"
```

You now have a ready-to-use workflow name!


## Minimal example (Prefect vs. Simmate)

It's useful to know how Prefect workflows compare to Simmate workflows. For
simple cases where you have python code, you'd define a Prefect workflow
like so:

``` python
from prefect import flow

@flow
def my_favorite_workflow():
    print("This workflow doesn't do much")
    return 42

# and then run your workflow
state = my_favorite_workflow()
result = state.result()
```

To convert this to a Simmate workflow, we just need to change the format
a little. Instead of a `@flow` decorator, we use the `run_config` method
of a new subclass:

``` python
# NOTE: this example does not follow Simmate's naming convention, so
# some higher level features will be broken. We will fix in a later step.

from simmate.workflow_engine import Workflow

class Example__Python__MyFavoriteSettings(Workflow):

    @staticmethod
    def run_config():
        print("This workflow doesn't do much")
        return 42

# and then run your workflow
state = MyFavoriteWorkflow.run()
result = state.result()
```

Behind the scenes, the `run` method is converting our `run_config` to a
Prefect workflow for us.


### Full example

Now let's look at a realistic example where we build a Workflow that has
input parameters and accesses class attributes/methods:

``` python

class Example__Python__MyFavoriteSettings(Workflow):

    example_constant = 12

    @staticmethod
    def squared(x):
        return x ** 2

    @classmethod
    def run_config(cls, name, say_hello=True, **kwargs):

        if say_hello:
            print(f"Hello and welcome, {name}!")

        # grab class values and methods
        x = cls.example_constant
        example_calc = cls.squared(x)
        print(f"Our calculation gave a result of {example_calc}")

        # grab extra arguments if you need them
        for key, value in kwargs.items():
            print(
                f"An extra parameter for {key} was given "
                "with a value of {value}"
            )

        return "Success!"
```

## Single S3Task + DatabaseTable

In many cases, you may have a workflow that runs a single calculation
and then writes the results to a specific database table. An example of
this would be an energy calculation using VASP. For common tasks
like this, the Workflow class is pre-configured to take an `S3Task`
and `DatabaseTable` -- including a default `run_config` method for you.
You can build your workflow like so:
    
``` python
from simmate.workflow_engine import Workflow

from my_app.tasks import ExampleS3Task
from my_app.models import ExampleTable

class Example__Python__MyFavoriteSettings(Workflow):
    s3task = ExampleS3Task
    database_table = ExampleTable

# try your workflow!
state = Example__Python__MyFavoriteSettings.run()
result = state.result()
```

To learn more about making the S3Task and DatabaseTable, make sure you
have gone through all the Simmate 
[tutorials](https://github.com/jacksund/simmate/tree/main/tutorials), 
including the advanced "Creating custom workflows" tutorial.
"""

import logging
import json
import cloudpickle
import yaml
import re
import inspect
from typing import List, Any
import uuid
from pathlib import Path

import simmate
from simmate.database.base_data_types import Calculation
from simmate.utilities import get_directory, copy_directory
from simmate.workflow_engine.execution import SimmateExecutor, WorkItem


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
    An abstract base class for all Simmate workflows. Default methods are configured
    for use with S3Tasks and Workflows.
    """

    # TODO: set storage attribute to module

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
    
    This includes calling the `_register_calculation` and `_save_to_database`
    methods attached to this workflow.
    
    `_register_calculation` will save a database entry before the workflow
    starts. This is useful to keep track of workflows that have been
    submitted/started but haven't finished yet.
    
    `_save_to_database` saves the output of the `workup` method to the database.
    """

    _parameter_methods = ["run_config"]
    """
    List of methods that allow unique input parameters. This helps track where
    `**kwargs` are passed and let's us gather the inputs in one place.
    """

    # -------------------------------------------------------------------------
    # Core methods that handle how and what a workflow run does
    # and how it is submitted
    # -------------------------------------------------------------------------

    @classmethod
    def run_config(cls):
        """
        The workflow method, which can be overwritten when inheriting from this
        class. This can be either a staticmethod or classmethod.
        """
        raise NotImplementedError(
            "When creating a custom workflow, make sure you set a run_config method!"
        )

    @classmethod
    def _run_full(cls, run_id=None, **kwargs):
        """
        This method should not be called directly. Use the `run` method instead.
        """
        logging.info(f"Starting {cls.name_full}")
        # This method is isolated only because we want to wrap it as a prefect
        # workflow in some cases.
        run_id = run_id or cls._get_run_id()
        kwargs_cleaned = cls._load_input_and_register(run_id=run_id, **kwargs)
        result = cls.run_config(**kwargs_cleaned)
        if cls.use_database:
            result["calculation_id"] = cls._save_to_database(result, run_id=run_id)
        logging.info(f"Completed {cls.name_full}")
        return result

    @staticmethod
    def _get_run_id():
        """
        generates a random id to use as a workflow run id
        """
        # This is a separate method in order to allow the prefect executor to
        # overwrite this method.
        unique_id = str(uuid.uuid4())
        return unique_id

    @classmethod
    def run(cls, **kwargs) -> DummyState:
        """
        runs the workflow locally
        """
        # Note: this is a separate method and wrapper around run_full because
        # we want to allow Prefect executor to overwrite this method.
        result = cls._run_full(**kwargs)
        state = DummyState(result)
        return state

    @classmethod
    def run_cloud(cls, return_future: bool = True, **kwargs) -> str:
        """
        submits the workflow run to cloud database to be ran by a worker
        """

        logging.info(f"Submitting new run of {cls.name_full} to cloud")

        # If we are submitting using a filename, we don't want to
        # submit to a cluster and have the job fail because it doesn't have
        # access to the file. We therefore deserialize right before
        # serializing in the next line in order to ensure parameters that
        # accept file names are submitted with all necessary data.
        parameters_deserialized = cls._deserialize_parameters(**kwargs)
        parameters_serialized = cls._serialize_parameters(**parameters_deserialized)

        # Because we often want to save some info to our database even before
        # the calculation starts/finishes, we do that by calling _register_calc
        # at this higher level. An example is storing the structure and run id.
        # Thus, we create and register the run_id up front
        run_id = cls._get_run_id()
        cls._register_calculation(run_id=run_id, **kwargs)

        future = SimmateExecutor.submit(
            cls._run_full,  # should this be the run method...?
            run_id=run_id,
            tags=cls.tags,
            **parameters_serialized,
        )

        logging.info(f"Successfully submitted (run_id={run_id})")

        # If the user wants the future, return that instead of the run_id
        if return_future:
            return future

        return run_id

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
        return WorkItem.objects.filter(status__in=["P", "R"], tags=cls.tags).count()

    # -------------------------------------------------------------------------
    # Methods that help with accessing the database and saving results
    # -------------------------------------------------------------------------

    @classmethod
    @property
    def database_table(cls) -> Calculation:
        """
        The database table where calculation information (such as the run_id)
        is stored. The table should use `simmate.database.base_data_types.Calculation`

        In many cases, this table will contain all of the results you need. However,
        pay special attention to NestedWorkflows, where your results are often tied
        to a final task.
        """
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
                from simmate.database.base_data_types import (
                    DensityofStatesCalc,
                )

                return DensityofStatesCalc
        elif flow_type == "population-analysis":
            from simmate.database.base_data_types import PopulationAnalysis

            return PopulationAnalysis
        elif flow_type == "dynamics":
            from simmate.database.base_data_types import DynamicsRun

            return DynamicsRun
        elif flow_type == "diffusion":
            if "from-images" in flow_preset:
                from simmate.database.base_data_types import MigrationImage

                return MigrationImage
            else:
                from simmate.database.base_data_types import DiffusionAnalysis

                return DiffusionAnalysis
        elif flow_type == "customized":
            from simmate.database.base_data_types import CustomizedCalculation

            return CustomizedCalculation
        else:
            raise NotImplementedError("Unable to detect proper database table")

    @classmethod
    def _save_to_database(cls, result, run_id):

        # split our results and corrections (which are given as a dict) into
        # separate variables
        vasprun = result["result"]
        corrections = result["corrections"]
        directory = result["directory"]

        # load the calculation entry for this workflow run. This should already
        # exist thanks to the load_input_and_register task.
        calculation = cls.database_table.from_run_context(
            run_id=run_id,
            workflow_name=cls.name_full,
        )

        # now update the calculation entry with our results
        calculation.update_from_vasp_run(vasprun, corrections, directory)

        return calculation.id

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

    @classmethod
    @property
    def tags(cls) -> list[str]:
        """
        Lists of tags to submit a the workflow with when using run_cloud.
        """
        return [
            "simmate",
            cls.name_type,
            cls.name_calculator,
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
        return cls.__doc__

    @classmethod
    @property
    def parameter_names(cls) -> List[str]:
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
    def parameter_names_required(cls) -> List[str]:
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
        print(yaml.dump(cls.parameter_names))

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
    def _load_input_and_register(cls, run_id: str, **parameters: Any) -> dict:
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
        Even though all of these inputs are accepted, `workflow.run` always expects
        python objects, so this utility converts the input to a toolkit Structure
        object.

        `register_run` allows us to skip the database step if the database_table
        isn't properly set yet. This input is a temporary fix for the
        diffusion/from-images workflow.

        `copy_previous_directory` is only used when we are pulling a structure from a
        previous calculation. If copy_previous_directory=True, then the directory
        parameter is ignored.

        `**parameters` includes all parameters and anything extra that you want saved
        to simmate_metadata.yaml
        """

        # OPTIMIZE: consider splitting this task into load_structure, load_directory,
        # and register_calc so that our flow_visualize looks cleaner

        # OPTIMIZE: Customized workflows cause a lot of special handling in this task
        # so it may be worth isolating these into a separate task.

        # ---------------------------------------------------------------------

        # STEP 1: clean parameters

        parameters_cleaned = cls._deserialize_parameters(**parameters)

        # ---------------------------------------------------------------------

        # STEP 1b: Determine the "primary" input to use for setting the
        # source (and previous directory)
        # OPTIMIZE: Is there a better way to do this?

        # Currently I just set a priority of possible parameters that can be
        # the primary input. I go through each one at a time until I find one
        # that was provided -- then I exit with that parameter's value.
        primary_input = None
        for primary_input_key in [
            "structure",
            "migration_hop",
            "supercell_start",
        ]:
            primary_input = parameters.get(primary_input_key, None)
            primary_input_cleaned = parameters_cleaned.get(primary_input_key, None)
            if primary_input:
                break

        # ---------------------------------------------------------------------

        # STEP 2: Load the directory (and copy over from an old directory if necessary)

        # Start by creating a new directory or grabbing the one given. We create
        # this directory immediately (rather than just passing the name to the
        # S3Task). We do this because NestedWorkflows often use a parent directory
        # to organize results.
        directory = parameters.get("directory", None)
        directory_cleaned = get_directory(directory)

        # if the user requested, we grab the previous directory as well
        copy_previous_directory = parameters.get("copy_previous_directory", None)
        if copy_previous_directory:

            if not primary_input:
                raise Exception(
                    "No primary input detected, which is required for copying "
                    "past directories. This is an experimental feature so "
                    "please contact our team for more help."
                )

            # catch incorrect use of this function
            if not primary_input_cleaned.is_from_past_calc:
                raise Exception(
                    "There isn't a previous directory available! Your source "
                    "structure must point to a past calculation to use this feature."
                )

            # the past directory should be stored on the input object
            previous_directory = Path(primary_input_cleaned.database_object.directory)

            # Copy over all files except simmate ones (we have no need for the
            # summaries or error archives)
            copy_directory(
                directory_old=previous_directory,
                directory_new=directory_cleaned,
                ignore_simmate_files=True,
            )

        # SPECIAL CASE for customized flows
        if "workflow_base" not in parameters_cleaned:
            parameters_cleaned["directory"] = directory_cleaned
        else:
            parameters_cleaned["input_parameters"]["directory"] = directory_cleaned

        # ---------------------------------------------------------------------

        # STEP 3: Load the source of the input object

        source = parameters.get("source", None)

        # If we were given a input from a previous calculation, the source should
        # point directory to that same input. Otherwise we are incorrectly trying
        # to change what the source is.
        # "primary_input and" is added to the start to ensure cleaned input exists
        # and therefore prevent an error/bug.
        if source and primary_input and primary_input_cleaned.is_from_past_calc:
            # note primary_input here is a dictionary
            # assert
            if not source == primary_input:
                # only warning for now because this is experimental
                logging.warn(
                    "Your source does not match the source of your "
                    "primary input. Sources are an experimental feature, so "
                    "this will not affect your results. Still, please report "
                    "this to our team to help with development. \n\n"
                    f"SOURCE: {source} \n\n"
                    f"PRIMARY_INPUT: {primary_input} \n\n"
                )
            source_cleaned = source
        # Check if we have a primary input loaded from a past calculation and
        # default to that as the source.
        elif primary_input and primary_input_cleaned.is_from_past_calc:
            source_cleaned = primary_input
        # Otherwise just use the source given
        elif source:
            source_cleaned = source
        else:
            source_cleaned = None

        # SPECIAL CASE for customized flows
        if "workflow_base" not in parameters_cleaned:
            parameters_cleaned["source"] = source_cleaned
        else:
            parameters_cleaned["input_parameters"]["source"] = source_cleaned

        # ---------------------------------------------------------------------

        # STEP 4: Register the calculation so the user can follow along in the UI
        # and also see which structures/runs have been submitted aready.

        if cls.use_database:
            cls._register_calculation(run_id=run_id, **parameters_cleaned)

        # ---------------------------------------------------------------------

        # STEP 5: Write metadata file for user reference

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
            workflow_name=cls.name_full,
            # this ID is ingored as an input but needed for loading past data
            run_id=run_id,
            **parameters_serialized,
        )

        # now write the summary to file in the same directory as the calc.
        input_summary_filename = directory_cleaned / "simmate_metadata.yaml"
        with input_summary_filename.open("w") as file:
            content = yaml.dump(input_summary)
            file.write(content)

        # ---------------------------------------------------------------------

        # Finally we just want to return the dictionary of cleaned parameters
        # to be used by the workflow
        return parameters_cleaned

    @classmethod
    @property
    def _parameters_to_register(cls) -> List[str]:
        """
        A list of input parameters that should be used to register the calculation.
        """

        # run is always used to register but is never an input parameter
        parameters_to_register = []
        # run_id and workflow_name are used to register but these are
        # implemented with the _register_calculation elsewhere

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
    def _register_calculation(cls, run_id=None, **kwargs) -> Calculation:
        """
        If the workflow is linked to a calculation table in the Simmate database,
        this adds the flow run to the database.

        Parameters passed should be deserialized and cleaned.

        This method should not be called directly as it is used within the
        `run_prefect_cloud` method and `load_input_and_register` task.
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
            raise Exception("Checking if this method is ever used")

            from prefect.context import FlowRunContext

            run_context = FlowRunContext.get()
            workflow = run_context.flow.simmate_workflow
            database_table = workflow.database_table

        # Otherwise we should be using the subclass Workflow that has the
        # database_table property set.
        else:
            workflow = cls  # we have the workflow class already
            database_table = cls.database_table

        # Registration is only possible if a table is provided. Some
        # special-case workflows don't store calculation information bc the flow
        # is just a quick python analysis.
        if not database_table:
            logging.warn("No database table found. Skipping registration.")
            return

        # grab the registration kwargs from the parameters provided and then
        # convert them to a python object format for the database method
        register_kwargs = {
            key: kwargs.get(key, None) for key in workflow._parameters_to_register
        }
        register_kwargs_cleaned = cls._deserialize_parameters(
            add_defaults_from_attr=False, **register_kwargs
        )

        # SPECIAL CASE: for customized workflows we need to convert the inputs
        # back to json before saving to the database.
        if "workflow_base" in register_kwargs_cleaned:
            parameters_serialized = cls._serialize_parameters(**register_kwargs_cleaned)
            calculation = database_table.from_run_context(
                run_id=run_id,
                workflow_name=cls.name_full,
                **parameters_serialized,
            )
        else:
            # load/create the calculation for this workflow run
            calculation = database_table.from_run_context(
                run_id=run_id,
                workflow_name=cls.name_full,
                **register_kwargs_cleaned,
            )

        return calculation

    @staticmethod
    def _serialize_parameters(**parameters) -> dict:
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
                if hasattr(parameter_value, "as_dict"):
                    parameter_value = parameter_value.as_dict()
                elif hasattr(parameter_value, "to_dict"):
                    parameter_value = parameter_value.to_dict()
                elif parameter_key == "directory":
                    parameter_value = str(parameter_value)  # convert Path to str

                # workflow_base and input_parameters are special cases that
                # may require a refactor (for customized workflows)
                elif parameter_key == "workflow_base":
                    parameter_value = parameter_value.name_full
                elif parameter_key == "input_parameters":
                    # recursive call to this function
                    parameter_value = Workflow._serialize_parameters(**parameter_value)

                else:
                    parameter_value = cloudpickle.dumps(parameter_value)
            parameters_serialized[parameter_key] = parameter_value
        return parameters_serialized

    @classmethod
    def _deserialize_parameters(
        cls,
        add_defaults_from_attr: bool = True,
        **parameters,
    ) -> dict:
        """
        converts all parameters to appropriate python objects
        """

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

        # For a series of parameters, we want their default values to be loaded
        # from class attributes if they are not set. To do this, we first check
        # if the parameter is set in our kwargs dictionary and check if the
        # value is set to "None". If it is, then we change to the value set as
        # the class attribute.
        if add_defaults_from_attr:
            for parameter in cls.parameter_names:
                if parameters.get(parameter, None) == None and hasattr(cls, parameter):
                    parameters_cleaned[parameter] = getattr(cls, parameter)

        # The remaining checks look to intialize input to toolkit objects

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

        if parameters.get("directory", None):
            parameters_cleaned["directory"] = Path(parameters_cleaned["directory"])

        return parameters_cleaned
