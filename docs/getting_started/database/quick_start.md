# Database Exploration

!!! tip
    We recommend using [DBeaver](https://dbeaver.io/) to explore your database and all of its tables. DBeaver is free and production-ready for all database backends that we support (SQLite, Postgres, etc.).

## Quick Guide

1. Ensure your database is initialized. This was done in earlier tutorials with the command `simmate database reset`. Do **NOT** rerun this command as it will clear your database and erase your results.

2. (optional) Open up your database (`~/simmate/my_env-database.sqlite`) using [DBeaver](https://dbeaver.io/). Open and view the `workflows_staticenergy` table.

3. The results table for Tutorial 2 is found in the `StaticEnergy` datatable class, which can be accessed via either of these options:
```python
# OPTION 1
from simmate.database import connect # this connects to our database
from simmate.database.workflow_results import StaticEnergy

# OPTION 2
from simmate.workflows.utilities import get_workflow
workflow = get_workflow("static-energy.quantum-espresso.quality00")
table = workflow.database_table  # yields the StaticEnergy class
```

4. Use `show_columns` to see all available table columns:
``` python
table.show_columns()
```

5. Convert the full table to a pandas dataframe:
``` python
df = table.objects.to_dataframe()
```

6. Use [django-based queries](https://docs.djangoproject.com/en/4.0/topics/db/queries/) to filter results. For example:
```python
filtered_results = table.objects.filter(
    formula_reduced="NaCl", 
    nsites__lte=2,
).all()
```

7. Convert the final structure from a database object (aka `DatabaseStructure`) to a structure object (aka `ToolkitStructure`).
```python
single_relaxation = table.objects.filter(
    formula_reduced="NaCl", 
    nsites__lte=2,
).first()
nacl_structure = single_relaxation.to_toolkit()
```

8. Explore other tables and data available. For example, third-party data is automatically included in the prebuilt database (includes [Material Project](https://materialsproject.org/), [AFLOW](http://aflowlib.org/), [COD](http://www.crystallography.net/cod/), and more):
```python
from simmate.database import connect
from simmate.apps.jarvis.models import JarvisStructure

first_150_rows = JarvisStructure.objects.all()[:150]
dataframe = first_150_rows.to_dataframe()
```
