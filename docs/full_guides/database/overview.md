The Simmate Database
=====================

This module hosts everything for defining and interacting with your database.

For beginners, make sure you have completed [our database tutorial](https://github.com/jacksund/simmate/blob/main/tutorials/05_Search_the_database.md).

Submodules include...

- `base_data_types` : fundamental mix-ins for creating new tables
- `workflow_results` : collection of result tables for `simmate.workflows`
- `prototypes` : tables of prototype structures
- `third_parties` : loads data from external providers (such as Materials Project)

And there is one extra file in this module:

- `connect`: configures the database and installed apps (i.e. sets up Django)


Usage Notes
============

Accessing and analyzing data typically involves the following steps:

1. Connect to your database
2. Load your database table
3. Query and filter data
4. Convert data to desired format
5. Modify data via `simmate.toolkit` or [pandas.Dataframe](https://pandas.pydata.org/)

The sections below will guide you on performing each of these steps. But to place everything up-front, your final script may look something like this:

``` python
# Connect to your database
from simmate.database import connect

# Load your database table
from simmate.database.third_parties import MatprojStructure

# Query and filter data
results = MatprojStructure.objects.filter(
    nsites=3,
    is_gap_direct=False,
    spacegroup=166,
).all()

# Convert data to desired format
structures = results.to_toolkit()
dataframe = results.to_dataframe()

# Modify data
for structure in structures:
    # run your anaylsis/modifications here!
```

## Connect to your database

For interactive use, Django settings must be configured before any of these submodules can be imported. This can be done with...

``` python
# connect to the database
from simmate.database import connect

# and now you can import tables in this module
from simmate.database.workflow_results import MITStaticEnergy
```

If this is not done, you will recieve the following error:

``` python
ImproperlyConfigured: Requested setting INSTALLED_APPS, but settings are not
configured. You must either define the environment variable DJANGO_SETTINGS_MODULE 
or call settings.configure() before accessing settings.
```

## Load your database table

The location of your table will depend on what data you're trying to access. To search, you can explore the other modules within this one (see top of this page where there are list). 

Using Materials Project as an example, we can load the table using...
``` python
from simmate.database.third_parties import MatprojStructure
```

If you are accessing data from a specific workflow, then in addition to loading from the `workflow_results` module, most workflows have a `database_table` attribute that let you access the table as well:

``` python
# There are two ways to load a table from calculation results...

######## METHOD 1 ########
from simmate.workflows.static_energy import mit_workflow

table = mit_workflow.database_table


######## METHOD 2 ########
from simmate.database import connect
from simmate.database.workflow_results import MITStaticEnergy


# This line proves these tables are the same! In practice, you only need to
# load the table via one of these two methods -- whichever you prefer.
assert table == MITStaticEnergy
```


## Query and filter data

Simmate uses Django ORM under the hood, so it follows [the same API for making queries](https://docs.djangoproject.com/en/4.0/topics/db/queries/). Below we reiterate the most basic functionality, but full features are discussed in the [Django's Model-layer documentation](https://docs.djangoproject.com/en/4.0/#the-model-layer).

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

- `contains`, `in`, `gt`, `gte`, `lt`, `lte`, `range`, `isnull`

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

## Convert data to desired format

By default, Django returns your query results as a `queryset` (or `SearchResults` in simmate). This is a list of database objects. It is more useful to convert them to a pandas dataframe or to toolkit objects.
``` python
# Gives a pandas dataframe
df = MITStaticEnergy.objects.filter(...).to_dataframe()

# Gives a list of toolkit Structure objects
df = MITStaticEnergy.objects.filter(...).to_toolkit()
```

## Modify data

To modify and analyze data, see the [pandas](https://pandas.pydata.org/docs/) and `simmate.toolkit` documentation for more info.
