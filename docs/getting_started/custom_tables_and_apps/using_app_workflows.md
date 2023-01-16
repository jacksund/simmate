# Using App Workflows

-------------------------------------------------------------------------------

## Organizing app workflows

By default, Simmate searches for a `workflows.py` (or `workflows` module) within your
app and grabs **all** python classes within it -- assuming they are workflows you want registered. If you scripts contain non-workflow classes or even abstract base workflows, this can cause unexpected errors. You must therefore explicitly specify which workflows should be registered with your app.

!!! note
    If you are seeing `AttributeError: '...' object has no attribute 'name_full'`
    or `Exception: Make sure you are following Simmate naming conventions`, then
    you likely have misorganized your workflows.

### in workflows.py file

When you first create your project/app, you'll notice a single `workflows.py` file
that has the following near the top:

``` python
# -----------------------------------------------------------------------------
# Make sure to list out all workflows that you want registered
# -----------------------------------------------------------------------------

__all__ = [
    "Example__Python__MyExample1",
    "Relaxation__Vasp__MyExample2",
]
```

You must explicitly list out all workflows that you want registered if you stay
with a single `workflow.py` file format.

### in a workflows module

As your app grows, you may want to store your workflows in separate scripts or
submodules. You can do this by deleting the `workflows.py` and replacing it with
a folder named `workflows` that has the following organization:

``` bash
# rest of example_app is organized the same as before
example_app
└── workflows
    ├── __init__.py   # <-- file used for registration
    ├── example_1.py
    ├── example_2.py
    ├── example_3.py
    └── example_submodule
        ├── __init__.py
        ├── example_4.py
        └── example_5.py
```

Here, `example_N.py` files can be named whatever you'd like and do NOT require the
`__all__` tag to be set. This folder structure allows us to organize all of our workflows nicely.

Instead of the `__all__` tag, we can list out workflows to register in the 
`workflows/__init__.py`. We can use relative python imports to accomplish this
with minimal code:

``` python
# in workflows/__init__.py

from .example_1 import Example__Python__MyExample1
from .example_2 import Example__Python__MyExample2
from .example_3 import Example__Python__MyExample3

from .example_submodule.example_4 import Example__Python__MyExample4
from .example_submodule.example_5 import Example__Python__MyExample5
```

!!! example
    If you prefer to learn by example, you can take a look at Simmate's built-in
    `Vasp` app. The `workflows` module of this app is located 
    [here](https://github.com/jacksund/simmate/tree/main/src/simmate/apps/vasp/workflows).
    You can also see how our `workflows/__init__.py` file lists out all of our
    workflows that are registered ([here](https://github.com/jacksund/simmate/blob/main/src/simmate/apps/vasp/workflows/__init__.py))).

-------------------------------------------------------------------------------

## Basic use

On the surface, our workflows here behave exactly the same as they did before. We can run them with a yaml file or directly in python.

``` yaml
workflow_name: example_app/workflows:Example__Python__MyExample1
structure: NaCl.cif
input_01: 12345
input_02: true
```

However, now that they are in a Simmate Project and we registered the App, we
can access some extra features. First, we can just use the workflow name and
also access our workflow with the command line and `get_workflow` utilities:

=== "yaml"
    ``` yaml
    workflow_name: example.python.my-example1
    structure: NaCl.cif
    input_01: 12345
    input_02: true
    ```

=== "python"
    ``` python
    from simmate.workflows.utilities import get_workflow
    
    workflow = get_workflow("example.python.my-example1")
    workflow.run(
        structure="NaCl.cif",
        input_01=12345,
        input_02=true,
    )
    ```

Check and see your workflow listed now too:
=== "command line"
    ``` bash
    simmate workflows list-all
    ```

!!! danger
    Make sure you set the `__all__` attribute in your workflows.py file. Otherwise,
    workflows will not be found or other errors may occur. This should just be
    a list of the workflows you want registered.

-------------------------------------------------------------------------------

## Link Datatables to Workflows

To have a workflow use a custom database table, the following requirements must be
met:

- [x] the table must use the `Calculation` mix-in
- [x] the workflow must have `database_table` set to our table
- [x] the table and workflow must be registered (already completed)

Note that one our database tables and workflows already meet these conditions.

For `MyCustomTable1`, we can see it is using the `Calculation` mix-in in our `models.py` file:
``` python
class MyCustomTable1(Structure, Calculation):
    # ... custom columns hidden ...
```

This table has already been linked to a workflow too. In our `workflows.py` file, we can see the following:
``` python
class Example__Python__MyExample1(Workflow):
    database_table = MyCustomTable1
```

This is completes our check-list -- so this database and workflow are already configured for us.

-------------------------------------------------------------------------------

## Storing inputs parameters

To have a workflow store input parameters at the start of a calculation, the following requirements must be met:

- [x] the parameter must have been added as a column to the database
- [x] a parameter **of the same exact name** must be an input option of `run_config`

For our `MyCustomTable1` and `Example__Python__MyExample1`, we can see that the following inputs
are matching for both the `run_config` input AND are table columns:

1. input_01
2. input_02
3. structure

Look through the relevant code that sets this up:

=== "MyCustomTable1"
    ```python
    # structure --> through the Structure mix-in
    input_01 = table_column.FloatField(null=True, blank=True)
    input_02 = table_column.BooleanField(null=True, blank=True)
    ```

=== "Example__Python__MyExample1"
    ```python
    def run_config(
        input_01,
        input_02,
        structure,
    ```

And that's it! You workflow will store these inputs to your database when
a workflow run starts.

-------------------------------------------------------------------------------

## Storing outputs and results

To have a workflow store outputs at the end of a calculation, the following requirements must be met:

- [x] the parameter must have been added as a column to the database
- [x] the `run_config` must return a dictionary of columns that need to be updated
- [x] a key **of the same exact name** must be in this dictionary

For our `MyCustomTable1` and `Example__Python__MyExample1`, we can see that the following outputs
are matching for both the `run_config`'s output dictionary AND are table columns:

1. output_01
2. output_02

Look through the relevant code that sets this up:

=== "MyCustomTable1"
    ```python
    output_01 = table_column.FloatField(null=True, blank=True)
    output_02 = table_column.BooleanField(null=True, blank=True)
    ```

=== "Example__Python__MyExample1"
    ```python
    return {
        "output_01": ...,
        "output_02": ...,
    }
    ```

And that's it! You workflow will store these results to your database when
a workflow run completes.

!!! tip
    Complex storing of results -- such as from toolkit objects or from files --
    is possible too. These are covered in the full guides.

-------------------------------------------------------------------------------

## Viewing Results

Results are stored the same as any other workflow. You'll see a summary file
written for you, and you can load all the data from you database. We only
configure a small number of columns for our workflow + datatable, but check
out all of the outputs!

``` yaml
_DATABASE_TABLE_: MyCustomTable1
_TABLE_ID_: 1
_WEBSITE_URL_: http://127.0.0.1:8000/workflows/example/python/my-example1/1
chemical_system: Cl-Na
computer_system: digital-storm
created_at: 2022-09-04 00:10:01.844798+00:00
density: 2.1053060843576104
density_atomic: 0.04338757298280908
directory: /home/jacksund/Documents/spyder_wd/simmate-task-ow6otw06
formula_anonymous: AB
formula_full: Na4 Cl4
formula_reduced: NaCl
id: 1
input_01: 12345.0
input_02: true
nelements: 2
nsites: 8
output_01: 1234500
output_02: false
run_id: 6872771c-c0d7-43b5-afea-b8ed87f6a5df
spacegroup_id: 225
updated_at: 2022-09-04 00:10:01.875757+00:00
volume: 184.38459332974767
volume_molar: 13.87987468758872
workflow_name: example.python.my-example1
workflow_version: 0.10.0
```

!!! danger
    The `_WEBSITE_URL_` is experimental and only works for common workflow
    types at the moment. In the future, you'll be able to explore your results
    in an automatically-built web interface.

-------------------------------------------------------------------------------
