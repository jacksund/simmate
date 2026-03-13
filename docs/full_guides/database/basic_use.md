# Basic Database Access

Analyzing data in Simmate follows a common workflow:

1. Establish a connection to your database.
2. Load the desired database table from an App.
3. Filter the data for specific results.
4. Convert results into Toolkit objects or DataFrames for analysis.

----------------------------------------------------------------------

## Quick Start Example

Here's a complete script illustrating how to filter and convert data from the Materials Project:

``` python
# 1. Connect to your database
from simmate.database import connect

# 2. Load a specific database table
from simmate.apps.materials_project.models import MatprojStructure

# 3. Filter data
results = MatprojStructure.objects.filter(
    nsites=3,
    is_gap_direct=False,
    spacegroup=166,
).all()

# 4. Convert data for analysis
structures = results.to_toolkit()
df = results.to_dataframe()

# 5. Analyze results
for structure in structures:
    print(structure.composition)
```

----------------------------------------------------------------------

## Connecting to Your Database

Before importing any submodules, you must configure Django settings for interactive use. Use the `connect` utility to do this:

``` python
from simmate.database import connect

# now you can import tables from any Simmate App
from simmate.database.workflow_results import Relaxation
```

!!! note
    `connect()` is a convenient shortcut for `simmate.config.django.setup()`. It initializes Simmate's settings and prepares the connection to your database.

----------------------------------------------------------------------

## Loading Your Database Table

In Simmate, every table is tied to an App. You import models from the app's `models` module:

``` python
# Accessing third-party data apps
from simmate.apps.materials_project.models import MatprojStructure

# Accessing workflow results
from simmate.database.workflow_results import Relaxation, StaticEnergy
```

If you're working with a specific workflow, you can often access its associated table directly via the `database_table` attribute:

``` python
from simmate.workflows.static_energy import mit_workflow
table = mit_workflow.database_table
```

----------------------------------------------------------------------

## Querying and Filtering Data

Simmate uses Django's [Object-Relational Mapper (ORM)](https://docs.djangoproject.com/en/5.2/topics/db/queries/) to perform complex queries.

### Basic Queries
Access all rows using the `all()` method:
``` python
MatprojStructure.objects.all()
```

Show all available columns for filtering:
``` python
MatprojStructure.show_columns()
```

### Exact Filtering
Filter rows with exact-value matches:
``` python
MatprojStructure.objects.filter(
    nsites=3,
    is_gap_direct=False,
    spacegroup=166,
).all()
```

### Conditional Filtering
Filter using conditions by chaining the column name with two underscores (`__`). Common conditions include:

- `gt` / `gte`: Greater than (or equal to)
- `lt` / `lte`: Less than (or equal to)
- `range`: Between two values
- `isnull`: Check if a value exists
- `icontains`: Case-insensitive text match

Example:
``` python
MatprojStructure.objects.filter(
    nsites__gte=3,            # 3 or more sites
    energy__isnull=False,     # must have an energy value
    density__range=(1, 5),    # density between 1 and 5 g/cm^3
    elements__icontains='"C"', # contains Carbon
    spacegroup__number=167,   # spacegroup 167 (R-3c)
).all()
```

!!! tip
    When filtering elements with SQLite (default), use double quotes inside single quotes like `'"C"'` to avoid matching partial strings like "Ca" or "Cl".

----------------------------------------------------------------------

## Converting Data

Query results return a `SearchResult` (a specialized Django `QuerySet`). You can convert these to common formats for analysis:

``` python
# Convert to a list of Simmate Toolkit objects (Structure, Molecule, etc.)
structures = MatprojStructure.objects.filter(...).to_toolkit()

# Convert to a DataFrame (polars or pandas)
df = MatprojStructure.objects.filter(...).to_dataframe()
```

----------------------------------------------------------------------
