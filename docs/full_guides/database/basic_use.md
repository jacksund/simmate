
# Basic Database Access

----------------------------------------------------------------------

## Outline of all steps

Accessing and analyzing data typically involves the following steps:

1. Connect to your database
2. Load a specific database table
3. Filter data
4. Convert data to a desired format
5. Modify data via `simmate.toolkit` or [pandas.Dataframe](https://pandas.pydata.org/)

The sections below will guide you on performing each step. But to place everything up-front, your final script may look like this:

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
    # run your anaylsis/modifications here!
```

----------------------------------------------------------------------

## Connect to your database

For interactive use, Django settings must be configured before any of these submodules can be imported. This can be done with...

``` python
# connect to the database
from simmate.database import connect

# and now you can import tables in this module
from simmate.database.workflow_results import MITStaticEnergy
```

If the `connect` step is not done, you will recieve the following error:

``` python
ImproperlyConfigured: Requested setting INSTALLED_APPS, but settings are not
configured. You must either define the environment variable DJANGO_SETTINGS_MODULE 
or call settings.configure() before accessing settings.
```

----------------------------------------------------------------------

## Load your database table

The name of your table will depend on the source you're trying to access. To see the available sources (Materials Project, OQMD, Jarvis, COD), you can explore the contents the [database/third_parties](https://github.com/jacksund/simmate/blob/main/src/simmate/database/third_parties/__init__.py) module.

Using Materials Project as an example, we can load the table using...
``` python
from simmate.database.third_parties import MatprojStructure
```

Alternatively, if you intend to access data from a specific workflow, there are two methods to access the table. in addition to loading from the `workflow_results` module, most workflows have a `database_table` attribute that let you access the table as well:

``` python
########## METHOD 1 ########

from simmate.workflows.static_energy import mit_workflow

table = mit_workflow.database_table


######## METHOD 2 ########

from simmate.database import connect
from simmate.database.workflow_results import MITStaticEnergy

# The line below shows that these tables are the same! Therfore, use
# whichever method you prefer.
assert table == MITStaticEnergy
```

----------------------------------------------------------------------

## Query and filter data

To query a table, Simmate inherits methods from Django, which is a web framework for quering massive datasets. It is powerful and efficient, and is therefore used to deliver data to many familiar websites, such as Instagram and Spotify. The key feature of Django that we use is its Object-Relational Mapper (ORM). The ORM allows us to use a simple language for making complex queries to our database. Below, we show some common queries. A full description of all query methods is discussed on [Django's query page](https://docs.djangoproject.com/en/4.0/topics/db/queries/).

All rows of the database table are available via the `objects` attribute:
``` python
MITStaticEnergy.objects.all()
```

All columns of the database table can be printed via the `show_columns` methods:
``` python
MITStaticEnergy.show_columns()
```

To filter rows with exact-value matches in a column:
``` python
MITStaticEnergy.objects.filter(
    nsites=3,
    is_gap_direct=False,
    spacegroup=166,
).all()
```

To filter rows based on conditions, chain the column name with two underscores. Conditions supported are listed [here](https://docs.djangoproject.com/en/4.0/ref/models/querysets/#field-lookups), but the most commonly used ones are:

- `contains` = contains text, case-sensitive query
- `icontains`= contains text, case-insensitive query
- `gt` = greater than
- `gte` =  greater than or equal to
- `lt` = less than
- `lte` = less than or equal to
- `range` = provides upper and lower bound of values
- `isnull` = returns `True` if the entry does not exist

An example query with conditional filters:
``` python
MITStaticEnergy.objects.filter(
    nsites__gte=3,  # greater or equal to 3 sites
    energy__isnull=False,  # the structure DOES have an energy
    density__range=(1,5),  # density is between 1 and 5
    elements__icontains='"C"',  # the structure includes the element Carbon
    spacegroup__number=167,  # the spacegroup number is 167
).all()
```

Note, for the filtering condition `elements__icontains`, we used some odd quotations when querying for carbon: `'"C"'`. This is not a typo! The quotes ensure we don't accidentally grab Ca, Cs, Ce, Cl, and so on. This is an issue when you are using SQLite (the default datbase backend). If you are using Postgres, this line can change to the cleaner version `elements__contains="C"`.

----------------------------------------------------------------------

## Convert data to desired format

By default, Django returns your query results as a `queryset` (or `SearchResults` in simmate). This is a list of database objects. It is more useful to convert them to a pandas dataframe or to toolkit objects.
``` python
# Gives a pandas dataframe.
df = MITStaticEnergy.objects.filter(...).to_dataframe()

# Gives a list of toolkit Structure objects
df = MITStaticEnergy.objects.filter(...).to_toolkit()

# '...' are the set of filters selected from above.
```

----------------------------------------------------------------------

## Modify data

To modify and analyze data, see the [pandas](https://pandas.pydata.org/docs/) and `simmate.toolkit` documentation for more info.

----------------------------------------------------------------------
