# Basic Database Access

----------------------------------------------------------------------

## Overview

The process of accessing and analyzing data typically involves these steps:

1. Establish a connection to your database
2. Load a specific database table
3. Apply filters to the data
4. Convert the data to a desired format
5. Modify the data using `simmate.toolkit` or [pandas.Dataframe](https://pandas.pydata.org/)

The following sections will guide you through each of these steps. Here's an example of what your final script might look like:

``` python
# Connect to your database
from simmate.database import connect

# Load a specific database table
from simmate.database.third_parties import MatprojStructure

# Filter data
results = MatprojStructure.objects.filter(
    nsites=3,
    is_gap_direct=False,
    spacegroup=166,
).all()

# Convert data to a desired format
structures = results.to_toolkit()
dataframe = results.to_dataframe()

# Modify data
for structure in structures:
    # run your analysis/modifications here!
```

----------------------------------------------------------------------

## Connecting to Your Database

Before importing any submodules, you must configure Django settings for interactive use. Here's how to do it:

``` python
# connect to the database
from simmate.database import connect

# now you can import tables in this module
from simmate.database.workflow_results import MITStaticEnergy
```

If you forget the `connect` step, you'll encounter this error:

``` python
ImproperlyConfigured: Requested setting INSTALLED_APPS, but settings are not
configured. You must either define the environment variable DJANGO_SETTINGS_MODULE 
or call settings.configure() before accessing settings.
```

----------------------------------------------------------------------

## Loading Your Database Table

The name of your table depends on the source you're accessing. To see the available sources (Materials Project, OQMD, Jarvis, COD), explore the contents of the [database/third_parties](https://github.com/jacksund/simmate/blob/main/src/simmate/database/third_parties/__init__.py) module.

For example, to load a table from the Materials Project, use:
``` python
from simmate.database.third_parties import MatprojStructure
```

If you're accessing data from a specific workflow, you can access the table in two ways. Besides loading from the `workflow_results` module, most workflows have a `database_table` attribute that allows you to access the table:

``` python
########## METHOD 1 ########

from simmate.workflows.static_energy import mit_workflow

table = mit_workflow.database_table


######## METHOD 2 ########

from simmate.database import connect
from simmate.database.workflow_results import MITStaticEnergy

# The line below shows that these tables are the same! Therefore, use
# whichever method you prefer.
assert table == MITStaticEnergy
```

----------------------------------------------------------------------

## Querying and Filtering Data

Simmate uses Django's methods for querying a table, leveraging its Object-Relational Mapper (ORM) to make complex queries to our database. Below are some common queries. For a full list of query methods, refer to [Django's query page](https://docs.djangoproject.com/en/4.0/topics/db/queries/).

Access all rows of the database table via the `objects` attribute:
``` python
MITStaticEnergy.objects.all()
```

Print all columns of the database table using the `show_columns` methods:
``` python
MITStaticEnergy.show_columns()
```

Filter rows with exact-value matches in a column:
``` python
MITStaticEnergy.objects.filter(
    nsites=3,
    is_gap_direct=False,
    spacegroup=166,
).all()
```

Filter rows based on conditions by chaining the column name with two underscores. Supported conditions are listed [here](https://docs.djangoproject.com/en/4.0/ref/models/querysets/#field-lookups), but the most commonly used ones are:

- `contains` = contains text, case-sensitive query
- `icontains`= contains text, case-insensitive query
- `gt` = greater than
- `gte` =  greater than or equal to
- `lt` = less than
- `lte` = less than or equal to
- `range` = provides upper and lower bound of values
- `isnull` = returns `True` if the entry does not exist

Here's an example query with conditional filters:
``` python
MITStaticEnergy.objects.filter(
    nsites__gte=3,  # greater or equal to 3 sites
    energy__isnull=False,  # the structure DOES have an energy
    density__range=(1,5),  # density is between 1 and 5
    elements__icontains='"C"',  # the structure includes the element Carbon
    spacegroup__number=167,  # the spacegroup number is 167
).all()
```

Note: For the filtering condition `elements__icontains`, we used quotations when querying for carbon: `'"C"'`. This is to avoid accidentally grabbing Ca, Cs, Ce, Cl, etc. This is necessary when using SQLite (the default database backend). If you're using Postgres, you can use the cleaner version `elements__contains="C"`.

----------------------------------------------------------------------

## Converting Data to Desired Format

By default, Django returns your query results as a `queryset` (or `SearchResults` in simmate), which is a list of database objects. It's often more useful to convert them to a pandas dataframe or to toolkit objects.
``` python
# Gives a pandas dataframe.
df = MITStaticEnergy.objects.filter(...).to_dataframe()

# Gives a list of toolkit Structure objects
df = MITStaticEnergy.objects.filter(...).to_toolkit()

# '...' are the set of filters selected from above.
```

----------------------------------------------------------------------

## Modifying Data

For information on how to modify and analyze data, refer to the [pandas](https://pandas.pydata.org/docs/) and `simmate.toolkit` documentation.

----------------------------------------------------------------------