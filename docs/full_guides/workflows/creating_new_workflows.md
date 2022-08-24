
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

Together, example workflow names would be:
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
your workflow names. Hyphens are placed based on capital letters.

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


## Example workflow

To build a Simmate workflow, you can have ANY python code you'd like. The only
requirement is that you place that code inside a `run_config` method of a 
new subclass for `Workflow`:

``` python
from simmate.workflow_engine import Workflow

class Example__Python__MyFavoriteSettings(Workflow):
    
    use_database = False  # we don't have a database table yet

    @staticmethod
    def run_config(**kwargs):
        print("This workflow doesn't do much")
        return 42

# and then run your workflow
state = MyFavoriteWorkflow.run()
result = state.result()
```

Behind the scenes, the `run` method is converting our `run_config` to a 
workflow and doing extra setup tasks for us.

Now let's look at a realistic example where we build a Workflow that has
input parameters and accesses class attributes/methods:

``` python

class Example__Python__MyFavoriteSettings(Workflow):
    
    use_database = False # we don't have a database table yet
    example_constant = 12

    @staticmethod
    def squared(x):
        return x ** 2

    @classmethod
    def run_config(cls, name, say_hello=True, **kwargs):
        # Workflows can contain ANY python code!
        # In other words...
        #   "The ceiling is the roof" -Michael Jordan

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

Once you have your new workflow, you can run it as you would any other worfklow:

``` python
state = Example__Python__MyFavoriteSettings.run("Jack")
result = state.result()
```

## Default parameters and using kwargs

You'll notice in the workflow above that we used `**kwargs` in each of our
`run_config` methods -- and if you remove these, the workflow will fail. This
is because simmate adds default parameters to the `run_config` that can be used
by all workflows. These parameters are:

- `run_id`: a unique id to help with tracking a calculation
- `directory`: a unique foldername that the calculation will take place in
- `compress_output`: whether to compress the directory to a zip file when we're done
- `source`: where the input of this calculation came from (EXPERIMENTAL FEATURE)

You can use any of these inputs to help with your workflow. Most commonly, you
just use the `directory` input and just ignore the others by adding `**kwargs`.
It is important to note that `directory` is given as a 
[`pathlib.Path`](https://docs.python.org/3/library/pathlib.html) object.

``` python
from simmate.workflow_engine import Workflow

class Example__Python__MyFavoriteSettings(Workflow):
    
    use_database = False  # we don't have a database table yet

    @staticmethod
    def run_config(directory, **kwargs):
        
        # We use the unique directory to write outputs!
        # Recall that we have a pathlib.Path object.
        output_file = directory / "my_output.txt"
        
        with output_file.open("w") as file:
            file.write("Writing my output!")
        
        # If you don't like/know pathlib.Path, you can
        # convert the directory name back to a string
        output_filename = str(output_file)
        
        return "Done!"

```


## Modifying an existing workflow

You can use python inheritance to borrow utilities and settings from workflows.
However, make sure you are making copies of the original workflow settings!
If you modify them without making a copy, you'll be in a world of trouble.

``` python
from simmate.workflows.utilities import get_workflow

original_workflow = get_workflow("static-energy.vasp.matproj")


class StaticEnergy__Vasp__MyCustomPreset(original_workflow):

    version = "2022.07.04"

    incar = original_workflow.incar.copy()  # Make sure you copy!
    incar.update(
        dict(
            NPAR=1,
            ENCUT=-1,
        )
    )

# make sure we have new settings updated
# and that we didn't change the original
assert original_workflow.incar != StaticEnergy__Vasp__MyCustomPreset
```


## Linking a database table

Many of workflows will want to store common types of data (such as StaticEnergy
or Relaxation data). If you would like to use these tables automatically, you 
simply to make sure you `name_type` matches what is available!

For example, if we look at a static-energy calculation, you will see
the `StaticEnergy` database table is automatically used because the
name of our workflow starts with "StaticEnergy":

``` python
from simmate.database import connect
from simmate.database.workflow_results import StaticEnergy

# no work required! This line shows everything is setup and working
assert StaticEnergy__Vasp__MyCustomPreset.database_table == StaticEnergy
```

If you would like to build or use a custom database, you must first have
a registered `DatabaseTable` (this is covered in the main tutorials), and
then you can link the database table to your workflow directly. The only
other requiredment is that your database table uses the `Calculation`
database mix-in: 

``` python

from my_project.models import MyCustomTable

class Example__Python__MyFavoriteSettings(Workflow):
    database_table = MyCustomTable
```


## Registering your workflow

Registering your workflow so that you can access it in the UI requires you to
build a "simmate project". This is covered in the main tutorials.


## Common workflow types

In many cases, you may have a workflow that runs a single calculation
and then writes the results to a specific database table. An example of
this would be an energy calculation using VASP. If your workflow involves
calling another program, you should read about the `S3Workflow` which helps
with writing input files, calling other programs, and handling errors.
See the documentation for `simmate.workflow_engine.s3_workflow`.


# Prefect backend (experimental)

When you enable Prefect as your workflow executor, Workflows are converted into
Prefect Flows under the hood, so having knowledge of Prefect can be useful in 
advanced cases. For advanced use or when building new features, we recommend 
going through the prefect tutorials located
[here](https://orion-docs.prefect.io/tutorials/first-steps/).


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
    def run_config(**kwargs):
        print("This workflow doesn't do much")
        return 42

# and then run your workflow
state = MyFavoriteWorkflow.run()
result = state.result()
```

Behind the scenes, the `run` method is converting our `run_config` to a
Prefect workflow for us. Methods like `run_cloud` will automatically use
Prefect now too.

This module defines the base class for all workflows in Simmate. When learning 
how use workflows, make sure you have gone through our intro 
[tutorials](https://github.com/jacksund/simmate/tree/main/tutorials). You
can then read through these guides for more features.



# Using existing workflows


## Loading a workflow

To import a specific workflow, see the `simmate.workflows` module. For all the
examples below, we will look at the `static-energy.vasp.matproj` workflow,
which we load with:
    
``` python
from simmate.workflows.all import StaticEnergy__Vasp__Matproj as workflow
```

Alternatively, you can also use `get_workflow` to load your workflow:
    
``` python
from simmate.workflows.utilities import get_workflow

workflow = get_workflow("static-energy.vasp.matproj")
```


## Viewing input parameters

A workflow's input parameters can be analyzed in the following ways:

``` python
workflow.show_parameters()  # prints out info
workflow.parameter_names
workflow.parameter_names_required
```


## Running a workflow (local)

To run a workflow locally (i.e. directly on your current computer), you can
use the `run` method. As a quick example:

``` python
state = workflow.run(
    structure="NaCl.cif", 
    command="mpirun -n 4 vasp_std > vasp.out",
)

if state.is_completed():  # optional check
    result = state.result()
```

Note that `run` returned a `State` object, not our result. States allows you to
check if the run completed successfully or not. Then final output of your
workflow run can be accessed using `state.result()`. The `State` is based off
of Prefect's state object, which you can read more about 
[here](https://orion-docs.prefect.io/concepts/states/). We use `State`s because 
the status of a run becomes important when we start scheduling runs to run
remotely, and more importantly, it allows use to building in compatibility with
other workflow engines like Prefect.

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

On the computer where you want to actually run the workflow, start a worker
that will pick up and run the workflow you just scheduled:

``` bash
# NOTE: This worker will run endlessly.
# To control shutdown, see the Worker documentation.
simmate workflow-engine start-worker
```

If you want better control of which workers select a given workflow, you can
use `tags` to label your submission and worker.

``` python
run_id = workflow.run_cloud(
    structure="NaCl.cif", 
    tags=["my-custom-tag1", "quick-job"]
)
```

``` bash
simmate workflow-engine start-worker -t my-custom-tag1 -t quick-job
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

You'll notice the table gives results for all runs of this type (e.g. all
static-energies). To limit your results to just this specific workflow, you
can use the `all_results` property:

``` python
results = workflow.all_results

# the line above is a shortcut for...
table = workflow.database_table
results = workflow.database_table.objects.filter(workflow_name=workflow.name_full)
```

Filtering of results is covered in the `simmate.database` documentation.

<!--
TODO:
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

Together, example workflow names would be:
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
your workflow names. Hyphens are placed based on capital letters.

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


## Example workflow

To build a Simmate workflow, you can have ANY python code you'd like. The only
requirement is that you place that code inside a `run_config` method of a 
new subclass for `Workflow`:

``` python
from simmate.workflow_engine import Workflow

class Example__Python__MyFavoriteSettings(Workflow):
    
    use_database = False  # we don't have a database table yet

    @staticmethod
    def run_config(**kwargs):
        print("This workflow doesn't do much")
        return 42

# and then run your workflow
state = MyFavoriteWorkflow.run()
result = state.result()
```

Behind the scenes, the `run` method is converting our `run_config` to a 
workflow and doing extra setup tasks for us.

Now let's look at a realistic example where we build a Workflow that has
input parameters and accesses class attributes/methods:

``` python

class Example__Python__MyFavoriteSettings(Workflow):
    
    use_database = False # we don't have a database table yet
    example_constant = 12

    @staticmethod
    def squared(x):
        return x ** 2

    @classmethod
    def run_config(cls, name, say_hello=True, **kwargs):
        # Workflows can contain ANY python code!
        # In other words...
        #   "The ceiling is the roof" -Michael Jordan

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

Once you have your new workflow, you can run it as you would any other worfklow:

``` python
state = Example__Python__MyFavoriteSettings.run("Jack")
result = state.result()
```

## Default parameters and using kwargs

You'll notice in the workflow above that we used `**kwargs` in each of our
`run_config` methods -- and if you remove these, the workflow will fail. This
is because simmate adds default parameters to the `run_config` that can be used
by all workflows. These parameters are:

- `run_id`: a unique id to help with tracking a calculation
- `directory`: a unique foldername that the calculation will take place in
- `compress_output`: whether to compress the directory to a zip file when we're done
- `source`: where the input of this calculation came from (EXPERIMENTAL FEATURE)

You can use any of these inputs to help with your workflow. Most commonly, you
just use the `directory` input and just ignore the others by adding `**kwargs`.
It is important to note that `directory` is given as a 
[`pathlib.Path`](https://docs.python.org/3/library/pathlib.html) object.

``` python
from simmate.workflow_engine import Workflow

class Example__Python__MyFavoriteSettings(Workflow):
    
    use_database = False  # we don't have a database table yet

    @staticmethod
    def run_config(directory, **kwargs):
        
        # We use the unique directory to write outputs!
        # Recall that we have a pathlib.Path object.
        output_file = directory / "my_output.txt"
        
        with output_file.open("w") as file:
            file.write("Writing my output!")
        
        # If you don't like/know pathlib.Path, you can
        # convert the directory name back to a string
        output_filename = str(output_file)
        
        return "Done!"

```


## Modifying an existing workflow

You can use python inheritance to borrow utilities and settings from workflows.
However, make sure you are making copies of the original workflow settings!
If you modify them without making a copy, you'll be in a world of trouble.

``` python
from simmate.workflows.utilities import get_workflow

original_workflow = get_workflow("static-energy.vasp.matproj")


class StaticEnergy__Vasp__MyCustomPreset(original_workflow):

    version = "2022.07.04"

    incar = original_workflow.incar.copy()  # Make sure you copy!
    incar.update(
        dict(
            NPAR=1,
            ENCUT=-1,
        )
    )

# make sure we have new settings updated
# and that we didn't change the original
assert original_workflow.incar != StaticEnergy__Vasp__MyCustomPreset
```


## Linking a database table

Many of workflows will want to store common types of data (such as StaticEnergy
or Relaxation data). If you would like to use these tables automatically, you 
simply to make sure you `name_type` matches what is available!

For example, if we look at a static-energy calculation, you will see
the `StaticEnergy` database table is automatically used because the
name of our workflow starts with "StaticEnergy":

``` python
from simmate.database import connect
from simmate.database.workflow_results import StaticEnergy

# no work required! This line shows everything is setup and working
assert StaticEnergy__Vasp__MyCustomPreset.database_table == StaticEnergy
```

If you would like to build or use a custom database, you must first have
a registered `DatabaseTable` (this is covered in the main tutorials), and
then you can link the database table to your workflow directly. The only
other requiredment is that your database table uses the `Calculation`
database mix-in: 

``` python

from my_project.models import MyCustomTable

class Example__Python__MyFavoriteSettings(Workflow):
    database_table = MyCustomTable
```


## Registering your workflow

Registering your workflow so that you can access it in the UI requires you to
build a "simmate project". This is covered in the main tutorials.


## Common workflow types

In many cases, you may have a workflow that runs a single calculation
and then writes the results to a specific database table. An example of
this would be an energy calculation using VASP. If your workflow involves
calling another program, you should read about the `S3Workflow` which helps
with writing input files, calling other programs, and handling errors.
See the documentation for `simmate.workflow_engine.s3_workflow`.
