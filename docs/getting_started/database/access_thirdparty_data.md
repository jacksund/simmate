## Accessing Third-Party Data

----------------------------------------------------------------------

## Intro to third-party data

There are many research teams in the larger community that have created databases consisting of over 100,000 structures, with calculations performed on each. In this section, we'll use Simmate to explore some of these datasets.

We'll begin with one of the smaller datasets: [JARVIS](https://jarvis.nist.gov/). Despite being smaller than others, it still contains approximately 56,000 structures.

In DBeaver, you can find this table at `data_explorer_jarvisstructure`.

----------------------------------------------------------------------

## Loading a Database

Previously, we loaded our `DatabaseTable` from the workflow. However, in this case, we want to directly access the JARVIS table. To do this, we run the following:

```python
from simmate.database import connect  # (1)
from simmate.database.third_parties import JarvisStructure
```

1. This configures all database tables and establishes a connection to your database. It must be ran before any tables are imported.

!!! warning 
    The most common error when loading database tables directly from the `simmate.database` module is forgetting to connect to your database. Don't forget to include `from simmate.database import connect`!

----------------------------------------------------------------------

## Populating Data

With our datatable class (`JarvisStructure`) loaded, let's check if it contains any data:

``` python
JarvisStructure.objects.count()
```

!!! note 
    If you accepted the download during the `simmate database reset` command, you should see thousands of structures already in this database table! 

If the count returns 0, it means you still need to load data. You can quickly load all the data using the `load_remote_archive` method. This method downloads the JARVIS data from simmate.org and transfers it to your database. This process can take approximately 10 minutes as it saves all these structures to your computer, enabling you to load these structures in under a second in the future.

``` python
JarvisStructure.load_remote_archive()
```

!!! warning
    Please read the warnings printed by `load_remote_archive`. This data was NOT created by Simmate. We are merely distributing it on behalf of other teams. Please credit them for their work!

----------------------------------------------------------------------

## Exploring the Data

Now that our database is populated with data, we can start exploring it:

``` python
data = JarvisStructure.objects.to_dataframe()[:150]  # (1)
```

1. We use [:150] to just show the first 150 rows

Let's test our filtering ability with this new data:

```python
from simmate.database import connect
from simmate.database.third_parties import JarvisStructure

# EXAMPLE 1: 
structures_1 = JarvisStructure.objects.filter(nsites__lt=6).all()  # (1)

# EXAMPLE 2:
structures_2 = JarvisStructure.objects.filter(  # (2)
   formula_full="Mo1 S2",
   density__lt=5,
   spacegroup__symbol="R3mH",
).all()

# Convert to Dataframes
df_1 = structures_1.to_dataframe()
df_2 = structures_2.to_dataframe()
```

1. all structures that have less than 6 sites in their unitcell
2. all MoS2 structures that are less than 5/A^3 and have a spacegroup symbol of R3mH

!!! tip 
    Note how we used `__lt` in our filter. `denity__lt=` translates to "less than this density:". There are many more filtered add-ons that you can use:

    - `contains` = contains text, case-sensitive query
    - `icontains`= contains text, case-insensitive query
    - `gt` = greater than
    - `gte` = greater than or equal to
    - `lt` = less than
    - `lte` = less than or equal to
    - `range` = provides upper and lower bound of values
    - `isnull` = returns True if the entry does not exist
    
    See the full guides for more information.

----------------------------------------------------------------------
