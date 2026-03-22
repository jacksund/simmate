# Creating New Workflows

!!! warning
    Class-based workflows *must* follow [Simmate naming conventions](naming_conventions.md) to work properly.

------------------------------------------------------------

## Using the `@workflow` Decorator

The easiest way to create a workflow is by using the `@workflow` decorator on a Python function. There are two steps to convert a function:

1. add the `@workflow` decorator
2. include `**kwargs` as an input

For example:

``` python
from simmate.workflows import workflow

@workflow
def add(x, y, **kwargs):
    return x + y

result = add.run(x=1, y=2)
```

The `@workflow` decorator also accepts several optional parameters to help with [naming conventions](naming_conventions.md) and database integration:

- `app_name`: The name of the app this workflow belongs to (defaults to "Basic")
- `type_name`: The type of analysis (defaults to "Toolkit")
- `use_database`: Whether to save results to a database table (defaults to `False`)

``` python
@workflow(
    app_name="Math",
    type_name="Basic",
    use_database=False,
)
def add(x, y, **kwargs):
    return x + y
```

------------------------------------------------------------

## Using Class-based Workflows

As you build more advanced workflows, you may want to switch to a class-based format. To do this, you must:

1. set the class name using Simmate conventions
2. define a `run_config` method
3. add `@staticmethod` or `@classmethod` to `run_config`
4. include `**kwargs` as an input to `run_config`

For example (using the same function as above):

``` python
from simmate.workflows import Workflow

class Math__Basic__Add(Workflow):

    use_database = False  # we don't have a database table yet

    @staticmethod
    def run_config(x, y, **kwargs):
        return x + y

result = Math__Basic__Add.run(x=1, y=2)
```

!!! tip
    Stick to `@workflow` for simple utilities. Class-based workflows are more important for sharing advanced features. For example, this is how we build reusable classes such as `VaspWorkflow` or `S3Workflow`, which are cover elsewhere in our guides.

!!! example

    Here's is a more advanced example that shows how class-based workflows can take advantage of other class methods:

    ``` python
    class Example__Python__Add100(Workflow):
        
        use_database = False # we don't have a database table yet

        constant = 100

        @classmethod
        def add_constant(cls, x):
            return x + cls.constant

        @classmethod
        def run_config(cls, x, **kwargs):
            return cls.add_constant(x)
    ```

    And also leverage class inheritance to reuse code:

    ``` python
    # we inherit from the class above!
    class Example__Python__Add300(Example__Python__Add100):
        constant = 300
    ```

------------------------------------------------------------

## Extra `**kwargs` Provided

Simmate automatically passes default parameters to your `run_config` or decorated function. These are used to track and organize the calculation:

- `run_id`: A unique ID for tracking the run (e.g., in the database).
- `directory`: The `pathlib.Path` where the calculation takes place.
- `compress_output`: Whether to zip the directory when finished.
- `source`: Information about where the inputs came from (experimental).

You should include `**kwargs` in your function signature to accept these parameters, even if you don't use them.

!!! example
    ``` python
    from simmate.workflows import workflow

    @workflow
    def example(run_id, **kwargs):
        print(run_id)
        print(**kwargs)  # to view others

    result = add.run()  # We don't have to provide `run_id`
    ```

------------------------------------------------------------

## Using `toolkit` Parameters

You often will use input parameters that correspond to `toolkit` objects, such as `Structure` or `Composition`. If you use the matching input parameter name, these will inherit all of their features -- such as loading from filename, a dictionary, or python object.

For example, if you use a `structure` input variable, it behaves as described in the [Parameters](/parameters.md) section.

``` python
from simmate.toolkit import Structure
from simmate.workflows import Workflow

class Example__Python__GetVolume(Workflow):
    
    use_database = False  # we don't have a database table yet

    @staticmethod
    def run_config(structure, **kwargs):
        assert type(structure) == Structure  # (1) 
        return structure.volume  # (2)
```

1. Even if we give a filename as an input, Simmate will convert it to a `toolkit` object for us
2. you can interact with the structure object because it is a `toolkit` object

!!! tip
    If you see a parameter in our documentation that has similar use to yours, make sure you use the same name. It can help with adding extra functionality.

------------------------------------------------------------

## Writing Output Files

Of all the default parameters (described above in `**kwargs`), you'll likely get the most from using the `directory` input. 

`directory` is given as a [`pathlib.Path`](https://docs.python.org/3/library/pathlib.html) object. Just add the directory to your `run_config()` method and use the object that's provided. For example:

``` python
from simmate.workflows import Workflow

class Example__Python__WriteFile(Workflow):
    
    use_database = False  # we don't have a database table yet

    @staticmethod
    def run_config(directory, **kwargs):
        output_file = directory / "my_output.txt" # (1)
        with output_file.open("w") as file:
            file.write("Writing my output!")
        return "Done!"

Example__Python__WriteFile.run()  # (2)
```

1. We use the `directory` created by Simmate and it will automatically be a `path.Pathlib` object
2. We don't need to define the `directory` as Simmate automatically builds one. We can, however, provide one if we wish.

------------------------------------------------------------

## Progam-specific Workflows

For many apps, there are workflow classes that you can use as a starting point. Make sure you explore the [Apps section](/apps/overview.md) of our documentation to see what is available.

For example, VASP users can inherit from the `VaspWorkflow` class, which includes many built-in features:

=== "basic VASP example"
    ``` python
    from simmate.apps.vasp.workflows.base import VaspWorkflow
    
    class Relaxation__Vasp__MyExample1(VaspWorkflow):
    
        functional = "PBE"
        potcar_mappings = {"Y": "Y_sv", "C": "C"}
    
        _incar = dict(
            PREC="Normal",
            EDIFF=1e-4,
            ENCUT=450,
            NSW=100,
            KSPACING=0.4,
        )
    ```

------------------------------------------------------------

## Building from Existing Workflows

Class-based workflows can leverage Python inheritance to borrow utilities and settings from an existing workflows.

Here is an example using a workflow from the `VASP` app:

``` python
from simmate.workflows.utils import get_workflow

original_workflow = get_workflow("static-energy.vasp.matproj")


class StaticEnergy__Vasp__MyCustomPreset(original_workflow):

    _incar_updates = dict(
        NPAR=1,
        ENCUT=-1,
    )
```

!!! note
    How you update a workflow depends on the app you are using. Be sure to read the [Apps section](/apps/overview.md) of our documentation for more information.

------------------------------------------------------------

## Linking a Database Table

Many workflows will want to store common types of data (such as static energy or relaxation data). If you want to use these tables automatically, you simply need to ensure your `name_type` matches what is available.

For example, if we look at a static-energy calculation, you will see the `StaticEnergy` database table is automatically used because the name of our workflow starts with `StaticEnergy`:

``` python
from simmate.database import connect
from simmate.database.workflow_results import StaticEnergy

assert StaticEnergy__Vasp__MyCustomPreset.database_table == StaticEnergy
```

If you want to build or use a custom database, you must first have a registered `DatabaseTable`, and then you can link the database table to your workflow directly. The only other requirement is that your database table uses the `Calculation` database mix-in:

``` python
from my_project.models import MyCustomTable

class Example__Python__MyFavoriteSettings(Workflow):
    database_table = MyCustomTable
```

------------------------------------------------------------

## Workflows that Call a Command

In many cases, you may have a workflow that runs a command or some external program and then reads the results from output files. An example of this would be an energy calculation using VASP. If your workflow involves calling another program, you should read about the "S3" workflow (`S3Workflow`) which helps with writing input files, calling other programs, and handling errors.

------------------------------------------------------------

## Registering Your Workflow

Registering your workflow so that you can access it in the UI requires you to build a "simmate project". This is covered in the getting-started tutorials.

------------------------------------------------------------
