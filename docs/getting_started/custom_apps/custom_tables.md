# Custom Database Tables

Simmate uses a **Django-based ORM** to manage its data. This means that you can create custom database tables using simple Python classes.

-------------------------------------------------------------------------------

## Defining a Table

In your Simmate App, you'll find a `models.py` file. This is where you define your database tables.

### Basic Table Example

``` python
from simmate.database.base_data_types import DatabaseTable, table_column

class MyResearchSample(DatabaseTable):
    sample_id = table_column.CharField(max_length=50)
    temperature = table_column.FloatField()
    is_pure = table_column.BooleanField(default=True)
```

-------------------------------------------------------------------------------

## Using Simmate Mixins

For scientific data, you often want to store things like crystal structures or calculation results. Simmate provides **mixins** that automatically add many useful columns to your tables.

### Scientific Table Example

``` python
from simmate.database.base_data_types import Structure, Calculation, table_column

class HighThroughputResult(Structure, Calculation):
    custom_input = table_column.FloatField()
    energy_per_atom = table_column.FloatField(null=True, blank=True)
```

By inheriting from `Structure` and `Calculation`, your table will automatically include columns for:

- Lattice parameters (a, b, c, alpha, beta, gamma)
- Volume and Density
- Chemical System and Composition
- Calculation status (running, completed, failed)
- Run ID and Directory
- Started and Finished timestamps

-------------------------------------------------------------------------------

## Applying Your Changes

After defining or updating your tables, you must update your database to reflect these changes:

``` bash
simmate database update
```

!!! note
    Behind the scenes, Simmate (via Django) creates "migration files" in your app's `migrations/` folder. These files track the history of your database schema.

-------------------------------------------------------------------------------

## Connecting a Table to a Workflow

The most powerful feature of custom tables is connecting them to a workflow. When you do this, Simmate will **automatically save the results** of every workflow run to your table.

### 1. Update the Workflow
In your app's `workflows.py`, set the `database_table` attribute on your workflow class:

``` python
from simmate.workflows import Workflow
from warren_app.models import HighThroughputResult

class My__Custom__Workflow(Workflow):
    database_table = HighThroughputResult  # <--- Connect the table!
    
    @staticmethod
    def run_config(structure, custom_input, **kwargs):
        # ... your workflow logic ...
        return {"energy_per_atom": -5.4321}
```

### 2. Run and Verify
Now, whenever you run this workflow, Simmate will create a new row in your table:

``` python
My__Custom__Workflow.run(structure="POSCAR", custom_input=1.23)
```

Check your database (e.g., using DBeaver) to see the newly created row with all the structure and calculation metadata automatically filled!

-------------------------------------------------------------------------------

## Searching and Filtering

Since your tables are standard Django models, you can easily search and filter them using Python:

``` python
from warren_app.models import HighThroughputResult

# Get all results with more than 10 atoms
results = HighThroughputResult.objects.filter(natoms__gt=10).all()

# Convert results to a Pandas DataFrame
df = results.to_dataframe()
```
