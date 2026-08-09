# Database Exploration

!!! tip
    We recommend using [DBeaver](https://dbeaver.io/) to explore your database and all of its tables. DBeaver is free and production-ready for all database backends that we support (SQLite, Postgres, etc.).

## Quick Guide

1. Ensure your database is initialized. This was done in earlier tutorials with the command `simmate database reset`. Do **NOT** rerun this command as it will clear your database and erase your results.

2. (optional) Open up your database (`~/simmate/my_env-database.sqlite3`) using [DBeaver](https://dbeaver.io/). Open and view the `workflows_staticenergy` table.

3. The results table for Tutorial 3 is found in the `StaticEnergy` datatable class, which can be accessed via either of these options:
```python
# OPTION 1: Direct import
from simmate.database import connect
from simmate.database.workflow_results import StaticEnergy

# OPTION 2: From the workflow object
from simmate.workflows.utils import get_workflow
workflow = get_workflow("static-energy.quantum-espresso.quality00")
table = workflow.database_table  # yields the StaticEnergy class
```

4. Use `show_columns` to see all available table columns for filtering:
``` python
StaticEnergy.show_columns()
```

5. Convert the full table (or a slice) to a pandas dataframe:
``` python
df = StaticEnergy.objects.to_dataframe()
```

6. Use [Django-based queries](https://docs.djangoproject.com/en/5.1/topics/db/queries/) to filter results. For example:
```python
filtered_results = StaticEnergy.objects.filter(
    formula_reduced="NaCl", 
    nsites__lte=2,
).all()
```

7. Convert database objects (rows) to toolkit objects (for analysis):
```python
# Convert a single row
single_result = filtered_results.first()
nacl_structure = single_result.to_toolkit()

# Convert a full list of results
structures = filtered_results.to_toolkit()
```

8. Explore third-party data. Simmate includes connectors for [Materials Project](https://materialsproject.org/), [AFLOW](http://aflowlib.org/), [COD](http://www.crystallography.net/cod/), and more:
```python
from simmate.database import connect
from simmate.apps.jarvis.models import JarvisStructure

# Grab the first 150 rows
dataframe = JarvisStructure.objects.all()[:150].to_dataframe()
```

!!! tip
    When filtering elements with the default SQLite backend, use double-quotes inside single-quotes: `elements__icontains='"C"'`. This ensures you match "C" (Carbon) and not "Ca" (Calcium) or "Cl" (Chlorine).
