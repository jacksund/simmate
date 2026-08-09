# Accessing Workflow Results

Simmate stores the results of its workflows in dedicated database tables. These tables are organized into Simmate Apps (like `vasp` or `quantum_espresso`).

----------------------------------------------------------------------

## Retrieving Results from Workflows

There are two primary ways to access the database table associated with a workflow:

### Method 1: Using the Workflow Object
Every Simmate workflow has a `database_table` attribute that points to its result table. This is the recommended method when you're already working with a workflow object.

``` python
from simmate.workflows.static_energy import vasp_mit_workflow

# Access the associated table
results_table = vasp_mit_workflow.database_table

# Query results
latest_results = results_table.objects.all()
```

### Method 2: Importing from the App's `models`
Alternatively, you can import the table directly from its Simmate App. This is the preferred method for scripts that only need to query data.

``` python
from simmate.database import connect
from simmate.database.workflow_results import StaticEnergy

# Query results
low_energy_entries = StaticEnergy.objects.filter(
    energy__lt=-1000
).all()
```

----------------------------------------------------------------------

## Shared Result Tables

To keep your database organized, many Simmate workflows share a single result table. For example, all VASP Static Energy workflows (like `vasp.mit` and `vasp.matproj`) store their results in the same `StaticEnergy` table within the `vasp` app.

You can distinguish results from different workflows using the `workflow_name` or `workflow_version` columns:

``` python
from simmate.database.workflow_results import StaticEnergy

# Filter for only results from the MIT workflow
mit_results = StaticEnergy.objects.filter(
    workflow_name="static-energy.vasp.mit"
).all()
```

----------------------------------------------------------------------

## Custom Result Tables

When you [build a custom workflow](../workflows/creating_basic_workflows.md), you can either reuse an existing Simmate table or define your own. For more details on defining new tables, see the [Creating New Tables](./creating_tables.md) guide.
