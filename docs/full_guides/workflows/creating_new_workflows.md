
# Creating new workflows

----------------------------------------------------------------------

## Create a workflow name

Build your workflow name using the Simmate conventions and run some checks to
make sure everything works as expected:
``` python
from simmate.workflow_engine import Workflow

class Example__Python__MyFavoriteSettings(Workflow):
    pass  # we will build the rest of workflow later

# These names can be long and unfriendly, so it can be nice to
# link them to a variable name for easier access.
my_workflow = Example__Python__MyFavoriteSettings

# Now check that our naming convention works as expected
assert my_workflow.name_full == "example.python.my-favorite-settings"
assert my_workflow.name_type == "example"
assert my_workflow.name_calculator == "python"
assert my_workflow.name_preset == "my-favorite-settings"
```

!!! warning
    Higher level features such as the website interface require that workflow names follow a certain format. If you skip this step, your workflows will fail and cause errors elsewhere.

!!! tip
    make sure you have read of "Workflow Names" documentation.

----------------------------------------------------------------------

## A basic workflow

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
        return 12345
```

!!! note
    Behind the scenes, the `run` method is converting our `run_config` to a 
    workflow and doing extra setup tasks for us.
    
!!! danger
    Note that we added `**kwargs` to our function input. This is required for
    your workflow to run. Make sure you read the "Default parameters" section
    below to understand why.

----------------------------------------------------------------------

## A pythonic workflow

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

!!! danger
    The `**kwargs` is still important here. Make sure we are adding it at the 
    end of our input parameters. (see the next section for why)

----------------------------------------------------------------------

## Default parameters and using kwargs

You'll notice in the workflows above that we used `**kwargs` in each of our
`run_config` methods, and if you remove these, the workflow will fail. This
is because simmate automatically passes default parameters to the `run_config` 
method -- even if you didn't define them as inputs. 

We do this to allow all workflows to access key information about the run. 
These parameters are:

- `run_id`: a unique id to help with tracking a calculation
- `directory`: a unique foldername that the calculation will take place in
- `compress_output`: whether to compress the directory to a zip file when we're done
- `source`: where the input of this calculation came from

You can use any of these inputs to help with your workflow. Or alternatively,
just add `**kwargs` to your function and ignore them.

----------------------------------------------------------------------

## Common input parameters

You often will use input parameters that correspond to `toolkit` objects, such
as `Structure` or `Composition`. If you use the matching input parameter name,
these will inherit all of their features -- such as loading from filename, a 
dictionary, or python object.

For example, if you use a `structure` input variable, it behaves as described
in the [Parameters](/parameters/) section.

``` python
from simmate.toolkit import Structure
from simmate.workflow_engine import Workflow

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
    if you see a parameter in our documentation that has similar use to yours,
    make sure you use the same name. It can help with adding extra functionality.

----------------------------------------------------------------------

## Writing output files

Of all the default parameters (described above), you'll most like get the most
from using the `directory` input. It is important to note that
 `directory` is given as a 
[`pathlib.Path`](https://docs.python.org/3/library/pathlib.html) object. Just
add directory to your run_config() method and then use the object that's provided.

For example, this workflow will write an output file to 
`simmate-task-12345/my_output.txt` (where the `simmate-task-12345` folder is
automatically set up by Simmate).

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

----------------------------------------------------------------------

## Building from existing workflows

For many calculators, there are workflow classes that you
can use as a starting point. For example, VASP users can inherit from the
`VaspWorkflow` class, which includes many features built-in:

=== "basic VASP example"
    ``` python
    from simmate.calculators.vasp.workflows.base import VaspWorkflow
    
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
    from simmate.calculators.vasp.workflows.base import VaspWorkflow
    from simmate.calculators.vasp.inputs.potcar_mappings import (
        PBE_ELEMENT_MAPPINGS,
    )
    from simmate.calculators.vasp.error_handlers import (
        Frozen,
        NonConverging,
        Unconverged,
        Walltime,
    )
    
    
    class Relaxation__Vasp__MyExample2(VaspWorkflow):

        functional = "PBE"
        potcar_mappings = PBE_ELEMENT_MAPPINGS  # (1)

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
    from simmate.calculators.vasp.inputs import Incar
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

Further, can use python inheritance to borrow utilities and settings from an
existing workflow:

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
    the "Creating S3 Workflows" and "Third-party Software" sections for more 
    information.

----------------------------------------------------------------------

## Linking a database table

Many of workflows will want to store common types of data (such as static energy
or relaxation data). If you would like to use these tables automatically, you 
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
a registered `DatabaseTable`, and then you can link the database table to 
your workflow directly. The only other requiredment is that your database table
uses the `Calculation` database mix-in: 

``` python
from my_project.models import MyCustomTable

class Example__Python__MyFavoriteSettings(Workflow):
    database_table = MyCustomTable
```

!!! tip
    See the "Getting Started" and "Database" tutorials for how to build a 
    custom database table.
    
!!! warning
    Make sure your table uses the `Calculation` mix-in so that the run 
    information can be stored properly

----------------------------------------------------------------------

## Workflows that call a command

In many cases, you may have a workflow that runs a command or some external
program and then reads the results from output files. An example of
this would be an energy calculation using VASP. If your workflow involves
calling another program, you should read about the `S3Workflow` which helps
with writing input files, calling other programs, and handling errors.

----------------------------------------------------------------------

## Registering your workflow

Registering your workflow so that you can access it in the UI requires you to
build a "simmate project". This is covered in the getting-started tutorials.

!!! note
    For now, you can treat this step as optional if you do **not** have any 
    custom database tables.

----------------------------------------------------------------------

## Running our custom workflow

Once you have your new workflow and registered it, you can run it as you would 
any other one.

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

----------------------------------------------------------------------

## Creating nested workflows

Because workflows can contain any python code, they can also make calls to
other workflows -- either via `run` or `run_cloud` methods

When using `run`, you often want workflows to share a working directory, so
that you can find the results all in one place.

``` python
from simmate.workflows.utilities import get_workflow
from simmate.workflow_engine import Workflow

class Example__Python__MyFavoriteSettings(Workflow):
    
    use_database = False  # we don't have a database table yet

    @staticmethod
    def run_config(structure, directory, **kwargs):
    
        # you can grab a workflow locally, attach one as a class
        # attribute, or anything else possible with python
        another_workflow = get_workflow("static-energy.vasp.mit")
        
        # And run the workflow how you would like. Here, we are
        # just running the workflow 10 times in row on different
        # perturbations or "rattling" of the original structure
        for n in range(10):
            structure.perturb(0.05)  # modifies in-place
            another_workflow.run(
                structure=structure,
                directory= directory / f"perturb_number_{n}",
            )
```

!!! warning
    when using `run_cloud` you should **NOT** share a working directory. This
    causes problems when you have computational resource scattered accross 
    different computers & file systems.
    See github [#237](https://github.com/jacksund/simmate/issues/237).

----------------------------------------------------------------------
