# Creating New Workflows

## Workflow Naming

To create a workflow name, adhere to the Simmate conventions and run checks to ensure everything operates as expected:

``` python
from simmate.engine import Workflow

class Example__Python__MyFavoriteSettings(Workflow):
    pass  # we will build the rest of workflow later

# Assign long and complex names to a variable for easier access.
my_workflow = Example__Python__MyFavoriteSettings

# Verify that our naming convention works as expected
assert my_workflow.name_full == "example.python.my-favorite-settings"
assert my_workflow.name_type == "example"
assert my_workflow.name_app == "python"
assert my_workflow.name_preset == "my-favorite-settings"
```

## Basic Workflow

To construct a Simmate workflow, you can use any Python code. The only requirement is that you place the code inside a `run_config` method of a new subclass for `Workflow`:

``` python
from simmate.engine import Workflow

class Example__Python__MyFavoriteSettings(Workflow):
    
    use_database = False  # we don't have a database table yet

    @staticmethod
    def run_config(**kwargs):
        print("This workflow doesn't do much")
        return 12345
```

!!! note
    Behind the scenes, the `run` method transforms our `run_config` into a workflow and performs additional setup tasks.

!!! danger
    We added `**kwargs` to our function input. This is required for your workflow to run. Make sure you read the "Default parameters" section below to understand why.

## Pythonic Workflow

Here's a realistic example where we construct a Workflow that has input parameters and accesses class attributes/methods:

``` python

class Example__Python__MyFavoriteSettings(Workflow):
    
    use_database = False # we don't have a database table yet
    example_constant = 12

    @staticmethod
    def squared(x):
        return x ** 2

    @classmethod
    def run_config(cls, name, say_hello=True, **kwargs):
        if say_hello:
            print(f"Hello and welcome, {name}!")

        # access class values and methods
        x = cls.example_constant
        example_calc = cls.squared(x)
        print(f"Our calculation gave a result of {example_calc}")

        # access extra arguments if needed
        for key, value in kwargs.items():
            print(
                f"An extra parameter for {key} was given "
                f"with a value of {value}"
            )

        return "Success!"
```

!!! danger
    The `**kwargs` is still crucial here. Make sure we are adding it at the end of our input parameters. (see the next section for why)

## Default Parameters and Using kwargs

In the workflows above, we used `**kwargs` in each of our `run_config` methods. If you remove these, the workflow will fail. This is because Simmate automatically passes default parameters to the `run_config` method -- even if you didn't define them as inputs. 

We do this to allow all workflows to access key information about the run. These parameters are:

- `run_id`: a unique id for tracking a calculation
- `directory`: a unique folder name where the calculation will take place
- `compress_output`: whether to compress the directory to a zip file when we're done
- `source`: where the input of this calculation came from

You can use any of these inputs to assist with your workflow. Alternatively, just add `**kwargs` to your function and ignore them.

## Common Input Parameters

You often will use input parameters that correspond to `toolkit` objects, such as `Structure` or `Composition`. If you use the matching input parameter name, these will inherit all of their features -- such as loading from filename, a dictionary, or python object.

For example, if you use a `structure` input variable, it behaves as described in the [Parameters](/simmate/parameters/) section.

``` python
from simmate.toolkit import Structure
from simmate.engine import Workflow

class Example__Python__MyFavoriteSettings(Workflow):
    
    use_database = False  # we don't have a database table yet

    @staticmethod
    def run_config(structure, **kwargs):
        
        # Even if we give a filename as an input, Simmate will convert it
        # to a python object for us
        assert type(structure) == Structure
        
        # and you can interact with the structure object as usual
        return structure.volume
```

!!! tip
    If you see a parameter in our documentation that has similar use to yours, make sure you use the same name. It can help with adding extra functionality.

## Writing Output Files

Of all the default parameters (described above), you'll likely get the most from using the `directory` input. It is important to note that `directory` is given as a [`pathlib.Path`](https://docs.python.org/3/library/pathlib.html) object. Just add the directory to your run_config() method and use the object that's provided.

For example, this workflow will write an output file to `simmate-task-12345/my_output.txt` (where the `simmate-task-12345` folder is automatically set up by Simmate).

``` python
from simmate.engine import Workflow

class Example__Python__MyFavoriteSettings(Workflow):
    
    use_database = False  # we don't have a database table yet

    @staticmethod
    def run_config(directory, **kwargs):
        
        # We use the unique directory to write outputs!
        # Recall that we have a pathlib.Path object.
        output_file = directory / "my_output.txt"
        
        with output_file.open("w") as file:
            file.write("Writing my output!")
        
        return "Done!"
```

## Building from Existing Workflows

For many apps, there are workflow classes that you can use as a starting point. For example, VASP users can inherit from the `VaspWorkflow` class, which includes many built-in features:

=== "basic VASP example"
    ``` python
    from simmate.apps.vasp.workflows.base import VaspWorkflow
    
    class Relaxation__Vasp__MyExample1(VaspWorkflow):
    
        functional = "PBE"
        potcar_mappings = {"Y": "Y_sv", "C": "C"}
    
        incar = dict(
            PREC="Normal",
            EDIFF=1e-4,
            ENCUT=450,
            NSW=100,
            KSPACING=0.4,
        )
    ```

=== "full-feature VASP example"
    ``` python
    from simmate.apps.vasp.workflows.base import VaspWorkflow
    from simmate.apps.vasp.inputs import PBE_POTCAR_MAPPINGS
    from simmate.apps.vasp.error_handlers import (
        Frozen,
        NonConverging,
        Unconverged,
        Walltime,
    )
    
    
    class Relaxation__Vasp__MyExample2(VaspWorkflow):

        functional = "PBE"
        potcar_mappings = PBE_POTCAR_MAPPINGS  # (1)

        incar = dict(
            PREC="Normal",  # (2)
            EDIFF__per_atom=1e-5,  # (3)
            ENCUT=450,
            ISIF=3,
            NSW=100,
            IBRION=1,
            POTIM=0.02,
            LCHARG=False,
            LWAVE=False,
            KSPACING=0.4,
            multiple_keywords__smart_ismear={  # (4)
                "metal": dict(
                    ISMEAR=1,
                    SIGMA=0.06,
                ),
                "non-metal": dict(
                    ISMEAR=0,
                    SIGMA=0.05,
                ),
            },
            # WARNING --> see "Custom Modifier"" tab for this to work
            EXAMPLE__multiply_nsites=8,  # (5)
        )
    
        error_handlers = [  # (6)
            Unconverged(),
            NonConverging(),
            Frozen(),
            Walltime(),
        ]
    ```

    1. You can use pre-set mapping for all elements rather than define them yourself
    2. Settings that match the normal VASP input are the same for all structures regardless of composition.
    3. Settings can also be set based on the input structure using built-in tags like `__per_atom`. Note the two underscores (`__`) signals that we are using a input modifier.
    4. The type of smearing we use depends on if we have a metal, semiconductor, or insulator. So we need to decide this using a built-in keyword modifier named `smart_ismear`. Because this handles the setting of multiple INCAR values, the input begins with `multiple_keywords` instead of a parameter name.
    5. If you want to create your own logic for an input parameter, you can do that as well. Here we are showing a new modifier named `multiply_nsites`. This would set the incar value of EXAMPLE=16 for structure with 2 sites (2*8=16). Note, we define how this modifer works and register it in the "Custom INCAR modifier" tab. Make sure you include this code as well.
    6. These are some default error handlers to use, and there are many more error handlers available than what's shown. Note, the order of the handlers matters here. Only the first error handler triggered in this list will be used before restarting the job

=== "Custom INCAR modifier"
      If you need to add advanced logic for one of your INCAR tags, you can register a keyword_modifier to the INCAR class like so:
    ``` python
    # STEP 1: define the logic of your modifier as a function
    # Note that the function name must begin with "keyword_modifier_"
    def keyword_modifier_multiply_nsites(structure, example_mod_input):
        # add your advanced logic to determine the keyword value.
        return structure.num_sites * example_mod_input
    
    # STEP 2: register modifier with the Incar class
    from simmate.apps.vasp.inputs import Incar
    Incar.add_keyword_modifier(keyword_modifier_multiply_nsites)
    
    # STEP 3: use your new modifier with any parameter you'd like
    incar = dict(
        "NSW__multiply_nsites": 2,
        "EXAMPLE__multiply_nsites": 123,
    )
    ```
    
    !!! danger
        Make sure this code is ran BEFORE you run the workflow. Registration is 
        reset every time a new python session starts. Therefore, we recommend 
        keeping your modifer in the same file that you define your workflow in.

You can also use Python inheritance to borrow utilities and settings from an existing workflow:

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

!!! danger
    Make sure you are making copies of the original workflow settings! If you modify them without making a copy, you'll actually be changing the original workflow settings. The `assert` check that we make in the example above is therefore **very** important.
    
!!! tip
    To gain more insight to workflows like this, you should read through **both**
    the "Creating S3 Workflows" and related "Apps" sections for more 
    information.

## Linking a Database Table

Many workflows will want to store common types of data (such as static energy or relaxation data). If you want to use these tables automatically, you simply need to ensure your `name_type` matches what is available!

For example, if we look at a static-energy calculation, you will see the `StaticEnergy` database table is automatically used because the name of our workflow starts with "StaticEnergy":

``` python
from simmate.database import connect
from simmate.database.workflow_results import StaticEnergy

# no work required! This line shows everything is setup and working
assert StaticEnergy__Vasp__MyCustomPreset.database_table == StaticEnergy
```

If you want to build or use a custom database, you must first have a registered `DatabaseTable`, and then you can link the database table to your workflow directly. The only other requirement is that your database table uses the `Calculation` database mix-in: 

``` python
from my_project.models import MyCustomTable

class Example__Python__MyFavoriteSettings(Workflow):
    database_table = MyCustomTable
```

## Workflows that Call a Command

In many cases, you may have a workflow that runs a command or some external program and then reads the results from output files. An example of this would be an energy calculation using VASP. If your workflow involves calling another program, you should read about the `S3Workflow` which helps with writing input files, calling other programs, and handling errors.

## Registering Your Workflow

Registering your workflow so that you can access it in the UI requires you to build a "simmate project". This is covered in the getting-started tutorials.

## Running Your Custom Workflow

Once you have your new workflow and registered it, you can run it as you would any other one.

=== "yaml"
    ``` yaml
    workflow_name: path/to/my/script.py:my_workflow_obj  # (1)
    
    # Example parameters from our "Basic Workflow" above
    name: Jack
    say_hello: true
    ```

    1. If your workflow is not regiestered, you need to provide the path to your
    python script (e.g. `my_script.py` file) and then the variable name that the
    workflow is stored as. The normal variable would be 
    `Example__Python__MyFavoriteSettings`, but in the python example, we set it
    to something shorter like `my_workflow` for convenience.

=== "python"
    ``` python
    # in the same file the workflow is defined in
    
    # These names can be long and unfriendly, so it can be nice to
    # link them to a variable name for easier access.
    my_workflow = Example__Python__MyFavoriteSettings
    
    # Here we use parameters from our "Basic Workflow" above
    state = my_workflow.run(
        name="Jack"
        say_hello=True,
    )
    result = state.result()
    ```

!!! example
    If you wrote your workflow in a file name `learning_simmate.py`, you could
    set the workflow_name to `learning_simmate.py:Example__Python__MyFavoriteSettings`.
    


Make sure you read the "common input parameters" section above. These let
us really take advantage of how we provide our input. For example, a
`structure` parameter will automatically accept filenames or database entries:

=== "yaml"
    ``` yaml
    workflow_name: path/to/my/script.py:my_workflow_obj
    
    # Automatic features!
    structure:
        database_table: MatProjStructure
        database_id: mp-123
    ```

=== "python"
    ``` python
    # in the same file the workflow is defined in
    state = my_workflow.run(
        structure={
            "database_table": "MatProjStructure",
            "database_id": "mp-123",
        }
    )
    result = state.result()
    ```


!!! warning 
    When switching from Python to YAML, make sure you adjust the input format
    of your parameters. This is especially important if you use python a `list` or
    `dict` for one of your input parameters. Further, if you have complex input
    parameters (e.g. nested lists, matricies, etc.), we recommend using a TOML
    input file instead.

    === "lists"
        ``` python
        # in python
        my_parameter = [1,2,3]
        ```
        ``` yaml
        # in yaml
        my_parameter:
            - 1
            - 2
            - 3
        ```
    
    === "dictionaries"
        ``` python
        # in python
        my_parameter = {"a": 123, "b": 456, "c": ["apple", "orange", "grape"]}
        ```
        ``` yaml
        # in yaml
        my_parameter:
            a: 123
            b: 456
            c:
                - apple
                - orange
                - grape
        ```
        ``` toml
        # in toml
        [my_parameter]
        a = 123
        b = 456
        c = ["apple", "orange", "grape"]
        ```
    
    === "nested lists"
        ``` python
        # in python
        my_parameter = [
            [1, 2, 3],
            [4, 5, 6],
            [7, 8, 9],
        ]
        ```
        ``` yaml
        # in yaml (we recommend switching to TOML!)
        my_parameter:
            - - 1
              - 2
              - 3
            - - 4
              - 5
              - 6
            - - 7
              - 8
              - 9
        ```
        ``` toml
        # in toml
        my_parameter = [
            [1, 2, 3],
            [4, 5, 6],
            [7, 8, 9],
        ]
        ```

    === "tuple"
        ``` python
        # in python
        my_parameter = (1,2,3)
        ```
        ``` yaml
        # in yaml
        my_parameter:
            - 1
            - 2
            - 3
        # WARNING: This will return a list! Make sure you call 
        #   `tuple(my_parameter)`
        # at the start of your workflow's `run_config` if you need a tuple.
        ```
        ``` toml
        # in toml
        my_parameter = [1, 2, 3]
        # WARNING: This will return a list! Make sure you call 
        #   `tuple(my_parameter)`
        # at the start of your workflow's `run_config` if you need a tuple.
        ```

    === "nested lists"
        ``` python
        # in python
        my_parameter = [
            [1, 2, 3],
            [4, 5, 6],
            [7, 8, 9],
        ]
        ```
        ``` yaml
        # in yaml (we recommend switching to TOML!)
        my_parameter:
            - - 1
              - 2
              - 3
            - - 4
              - 5
              - 6
            - - 7
              - 8
              - 9
        ```
        ``` toml
        # in toml
        my_parameter = [
            [1, 2, 3],
            [4, 5, 6],
            [7, 8, 9],
        ]
        ```

    === "tuple"
        ``` python
        # in python
        my_parameter = (1,2,3)
        ```
        ``` yaml
        # in yaml
        my_parameter:
            - 1
            - 2
            - 3
        # WARNING: This will return a list! Make sure you call 
        #   `tuple(my_parameter)`
        # at the start of your workflow's `run_config` if you need a tuple.
        ```
        ``` toml
        # in toml
        my_parameter = [1, 2, 3]
        # WARNING: This will return a list! Make sure you call 
        #   `tuple(my_parameter)`
        # at the start of your workflow's `run_config` if you need a tuple.
        ```