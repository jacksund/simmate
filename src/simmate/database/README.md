The Simmate Database
--------------------

This module hosts everything for defining and interacting with your database.

For beginners, make sure you have completed [our database tutorial](https://github.com/jacksund/simmate/blob/main/tutorials/05_Search_the_database.md).

Submodules include...

- `base_data_types` : fundamental mixins for creating new tables
- `local_calculations` : collection of result tables for `simmate.workflows`
- `prototypes` : tables of prototype structures
- `third_parties` : loads data from external providers (such as Materials Project)


Usage Notes
------------

Accessing and analyzing data typically involves the following steps:

1. Connecting to your database
2. Loading your database table class
3. Querying and filtering data
4. Converting data to desired format
5. Modifying data via `simmate.toolkit` or [pandas.Dataframe](https://pandas.pydata.org/)

## Configuring settings

For interactive use, Django settings must be configured before any of these submodules can be imported. This can be done with...

``` python
from simmate.shortcuts import setup  # configures Django

# and now you can import tables in this module
from simmate.database.local_calculations import MITStaticEnergy
```

If this is not done, you will recieve the following error:

``` python
ImproperlyConfigured: Requested setting INSTALLED_APPS, but settings are not configured. You must either define the environment variable DJANGO_SETTINGS_MODULE or call settings.configure() before accessing settings.
```

## Querying data

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

- contains
- in
- gt + gte (gt = "greater than"; gte = "greater than or equal to")
- lt + lte (gt = "less than"; gte = "less than or equal to")
- range
- isnull (checks if column has a value)

An example query with conditional filters:
``` python
MITStaticEnergy.objects.filter(
    nsites__gte=3,  # greater or equal to 3 sites
    energy__isnull=False,  # the structure DOES have a energy
    density__range=(1,5),  # density is between 1 and 5
    elements__contains="Ca",  # the structure includes the element Ca
).all()
```

# Converting data to desired format

By default, Django returns your query results as a `queryset` (or `SearchResults` in simmate). This is a list of database objects. It is more useful to convert them to a pandas dataframe or to toolkit objects.
``` python
# Gives a pandas dataframe
df = MITStaticEnergy.objects.filter(...).to_dataframe()

# Gives a list of toolkit Structure objects
df = MITStaticEnergy.objects.filter(...).to_toolkit()
```

To modify each of these, see the [pandas](https://pandas.pydata.org/docs/) and `simmate.toolkit` documentation for more info.
