# Database Exploration

## Quick Guide

1. Ensure your database is initialized. This was done in tutorial 2 with the command `simmate database reset`. Do NOT rerun this command as it will clear your database and erase your results.
2. Navigate to the `simmate.database` module to see all available tables.
3. The results table for Tutorial 2 is found in the `StaticEnergy` datatable class, which can be accessed via either of these options:
```python
# OPTION 1
from simmate.database import connect # this connects to our database
from simmate.database.workflow_results import StaticEnergy

# OPTION 2 (recommended for convenience)
from simmate.workflows.utilities import get_workflow
workflow = get_workflow("static-energy.vasp.mit")
table = workflow.database_table  # results here is the same thing as StaticEnergy above
```
4. Use `StaticEnergy.show_columns()` to see all possible table columns.
5. Convert the full table to a pandas dataframe with `StaticEnergy.objects.to_dataframe()`.
6. Use [django-based queries](https://docs.djangoproject.com/en/4.0/topics/db/queries/) to filter results. For example:
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
