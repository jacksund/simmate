# Using App Workflows

-------------------------------------------------------------------------------

## Organizing app workflows

Simmate automatically searches for a `workflows.py` (or `workflows` module) within your app and retrieves all Python classes within it, assuming they are workflows you want registered. However, if your scripts contain non-workflow classes or abstract base workflows, this can lead to unexpected errors. Therefore, you need to explicitly specify which workflows should be registered with your app.

!!! note
    If you encounter `AttributeError: '...' object has no attribute 'name_full'` or `Exception: Make sure you are following Simmate naming conventions`, it's likely that your workflows are misorganized.

### in workflows.py file

Upon creating your project/app, you'll find a single `workflows.py` file with the following at the top:

``` python
# -----------------------------------------------------------------------------
# List all workflows you want registered
# -----------------------------------------------------------------------------

__all__ = [
    "Example__Python__MyExample1",
    "Relaxation__Vasp__MyExample2",
]
```

You must explicitly list all workflows you want registered if you stick with a single `workflow.py` file format.

### in a workflows module

As your app expands, you might want to store your workflows in separate scripts or submodules. You can do this by replacing the `workflows.py` file with a `workflows` folder with the following structure:

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

Here, `example_N.py` files can be named as you wish and do NOT require the `__all__` tag. This folder structure allows for better workflow organization.

Instead of the `__all__` tag, we can list workflows to register in the `workflows/__init__.py` file. We can use relative Python imports to achieve this with minimal code:

``` python
# in workflows/__init__.py

from .example_1 import Example__Python__MyExample1
from .example_2 import Example__Python__MyExample2
from .example_3 import Example__Python__MyExample3

from .example_submodule.example_4 import Example__Python__MyExample4
from .example_submodule.example_5 import Example__Python__MyExample5
```

!!! example
    If you prefer learning by example, check out Simmate's built-in `Vasp` app. The `workflows` module of this app is located [here](https://github.com/jacksund/simmate/tree/main/src/simmate/apps/vasp/workflows). You can also see how our `workflows/__init__.py` file lists all of our registered workflows [here](https://github.com/jacksund/simmate/blob/main/src/simmate/apps/vasp/workflows/__init__.py)).

-------------------------------------------------------------------------------

## Basic use

Our workflows behave the same as before. We can run them with a YAML file or directly in Python.

``` yaml
workflow_name: example_app/workflows:Example__Python__MyExample1
structure: NaCl.cif
input_01: 12345
input_02: true
```

However, now that they are in a Simmate Project and we registered the App, we can access some extra features. We can use just the workflow name and also access our workflow with the command line and `get_workflow` utilities:

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

You can also see your workflow listed now:
=== "command line"
    ``` bash
    simmate workflows list-all
    ```

-------------------------------------------------------------------------------

## Link Datatables to Workflows

To use a custom database table in a workflow, the following conditions must be met:

- [x] the table must use the `Calculation` mix-in
- [x] the workflow must have `database_table` set to our table
- [x] the table and workflow must be registered (already completed)

Note that our database tables and workflows already meet these conditions.

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

This completes our checklist -- so this database and workflow are already configured for us.

-------------------------------------------------------------------------------

## Storing inputs parameters

To store input parameters at the start of a calculation in a workflow, the following conditions must be met:

- [x] the parameter must have been added as a column to the database
- [x] a parameter **with the exact same name** must be an input option of `run_config`

For our `MyCustomTable1` and `Example__Python__MyExample1`, we can see that the following inputs match both the `run_config` input AND are table columns:

1. input_01
2. input_02
3. structure

Here's the relevant code that sets this up:

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

That's it! Your workflow will store these inputs in your database when a workflow run starts.

-------------------------------------------------------------------------------

## Storing outputs and results

To store outputs at the end of a calculation in a workflow, the following conditions must be met:

- [x] the parameter must have been added as a column to the database
- [x] the `run_config` must return a dictionary of columns that need to be updated
- [x] a key **with the exact same name** must be in this dictionary

For our `MyCustomTable1` and `Example__Python__MyExample1`, we can see that the following outputs match both the `run_config`'s output dictionary AND are table columns:

1. output_01
2. output_02

Here's the relevant code that sets this up:

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

That's it! Your workflow will store these results in your database when a workflow run completes.

-------------------------------------------------------------------------------

## Viewing Results

Results are stored the same as any other workflow. You'll see a summary file written for you, and you can load all the data from your database. We only configure a small number of columns for our workflow + datatable, but check out all of the outputs!

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

-------------------------------------------------------------------------------