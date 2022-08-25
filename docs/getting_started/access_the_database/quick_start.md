
# Search the database

In this tutorial, you will learn how to explore your database as well as load data from third-party providers. Beginners will also be introduced to python inheritance.

!!! tip
    This entire tutorial should be ran on your local computer because we will be using Spyder. To use results from your remote calculations, you can copy/paste your database file from your remote computer to where our local database one should be (~/simmate/my_env-database.sqlite3). Note, copy/pasting will no longer be necessary when we switch to a cloud database in the next tutorial.

## The quick tutorial

1. Make sure you've initialized your database. This was done in tutorial 2 with the command `simmate database reset`. Do NOT rerun this command as it will empty your database and delete your results.
2. Go to the `simmate.database` module to view all available tables.
3. The table for Tutorial 2's results are located in the `StaticEnergy` datatable class, which can be loaded via either of these options:
```python
# OPTION 1
from simmate.database import connect # this connects to our database
from simmate.database.workflow_results import StaticEnergy

# OPTION 2 (recommended for convenience)
from simmate.workflows.utilities import get_workflow
workflow = get_workflow("static-energy.vasp.mit")
table = workflow.database_table  # results here is the same thing as StaticEnergy above
```
4. View all the possible table columns with `StaticEnergy.show_columns()`
5. View the full table as pandas dataframe with `StaticEnergy.objects.to_dataframe()`
6. Filter results using [django-based queries](https://docs.djangoproject.com/en/4.0/topics/db/queries/). For example:
```python
filtered_results = StaticEnergy.objects.filter(
    formula_reduced="NaCl", 
    nsites__lte=2,
).all()
```
7. Convert the final structure from a database object (aka `DatabaseStructure`) to a structure object (aka `ToolkitStructure`).
```python
single_relaxation = StaticEnergy.objects.filter(
    formula_reduced="NaCl", 
    nsites__lte=2,
).first()
nacl_structure = single_relaxation.to_toolkit()
```
8. For third-party data (like [Material Project](https://materialsproject.org/), [AFLOW](http://aflowlib.org/), [COD](http://www.crystallography.net/cod/), etc.) load the database table and then request to download all the available data:
```python
from simmate.database import connect  # this connects to our database
from simmate.database.third_parties import JarvisStructure

# NOTE: This line is only needed if you did NOT accept the download
# when running `simmate database reset`.
# This only needs to ran once -- then data is stored locally.
JarvisStructure.load_remote_archive()

# now explore the data (only the first 150 structures here)
first_150_rows = JarvisStructure.objects.all()[:150]
dataframe = first_150_rows.to_dataframe()
```

!!! warning
    To protect our servers, you can only call `load_remote_archive()` a few times per month. Don't overuse this feature.
