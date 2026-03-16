# Custom Apps Quickstart

This page provides a concise summary of creating a custom app, workflows, and database tables in Simmate.

-------------------------------------------------------------------------------

## 1. Create and Register an App

``` bash
# Create a new app project
simmate start-project my_project

# Update project name in pyproject.toml and renaming folder/apps.py
# (See 'Create a Custom App' page for details)

# Install the app
cd my_project
pip install -e .

# Register the app
simmate config add "example_app.apps.ExampleAppConfig"
```

-------------------------------------------------------------------------------

## 2. Define a Custom Table

In `models.py`:

``` python
from simmate.database.base_data_types import Structure, Calculation, table_column

class MyResultTable(Structure, Calculation):
    custom_field = table_column.FloatField()
    output_energy = table_column.FloatField(null=True, blank=True)
```

Apply changes:
``` bash
simmate database update
```

-------------------------------------------------------------------------------

## 3. Create a Custom Workflow

In `workflows.py`:

``` python
from simmate.workflows import Workflow
from example_app.models import MyResultTable

class My__Custom__Workflow(Workflow):
    database_table = MyResultTable
    
    @staticmethod
    def run_config(structure, custom_field, **kwargs):
        # ... logic ...
        return {"output_energy": -12.34}
```

-------------------------------------------------------------------------------

## 4. Run the Workflow

``` python
from example_app.workflows import My__Custom__Workflow

My__Custom__Workflow.run(structure="POSCAR", custom_field=1.0)
```

-------------------------------------------------------------------------------

## 5. Search Results

``` python
from example_app.models import MyResultTable

# Filter by structure properties or custom fields
results = MyResultTable.objects.filter(natoms__gt=10).all()
df = results.to_dataframe()
```
