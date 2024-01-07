## Accessing Third-Party Data

In order to perform calculations with Simmate, it's crucial to understand what calculations have already been performed by other researchers for a specific material. Numerous research teams globally have created databases consisting of over 100,000 structures, with calculations performed on each. In this section, we'll use Simmate to explore these databases.

## Loading a Database

We'll begin with one of the smaller databases: [JARVIS](https://jarvis.nist.gov/). Despite being smaller than others, it still contains approximately 56,000 structures. Simmate allows you to download all of these in under 0.01 GB.

Previously, we loaded our `DatabaseTable` from the workflow. However, in this case, we want to directly access the table. To do this, we execute the following:

```python
# This line MUST be executed before any tables can be loaded
from simmate.database import connect  # this connects to our database

# This provides the database_table we used in the previous section
from simmate.database.workflow_results import StaticEnergy

# This loads the table where we store all of the JARVIS data.
from simmate.database.third_parties import JarvisStructure
```

The `table` from the previous section (on accessing workflow data) and the `StaticEnergy` class here refer to the same class/table. These are just different methods of loading it. While loading a workflow automatically sets up a database connection, we have to manually perform this step here (with `from simmate.database import connect`). 

!!! warning 
    The most common error when loading database tables directly from the `simmate.database` module is forgetting to connect to your database. Don't forget to include `from simmate.database import connect`!

## Populating Data

With our datatable class (`JarvisStructure`) loaded, let's check if it contains any data:

``` python
JarvisStructure.objects.count()
```

!!! note 
    If you accepted the download during the `simmate database reset` command, you should see thousands of structures already in this database table! 

If the count returns 0, it means you still need to load data. You can quickly load all the data using the `load_remote_archive` method. This method downloads the JARVIS data from simmate.org and transfers it to your database. This process can take approximately 10 minutes as it saves all these structures to your computer, enabling you to load these structures in under a second in the future.

``` python
# NOTE: This line is only needed if you did NOT accept the download
# when running `simmate database reset`.
JarvisStructure.load_remote_archive()  # This may take ~10min to complete
```

!!! warning
    Please read the warnings printed by `load_remote_archive`. This data was NOT created by Simmate. We are merely distributing it on behalf of other teams. Please credit them for their work!

The `load_remote_archive` function downloads ALL data to your computer and saves it. This data will not be updated unless you call `load_remote_archive` again. This should only be done when we release a new archive version (usually once per year). **Avoid overusing this feature.**

## Exploring the Data

Now that our database is populated with data, we can start exploring it:

``` python
# We use [:150] to just show the first 150 rows
data = JarvisStructure.objects.to_dataframe()[:150]
```

Let's test our filtering ability with this new data:

```python
from simmate.database import connect  # this connects to our database
from simmate.database.third_parties import JarvisStructure

# EXAMPLE 1: all structures that have less than 6 sites in their unitcell
structures_1 = JarvisStructure.objects.filter(nsites__lt=6).all()

# EXAMPLE 2: all MoS2 structures that are less than 5/A^3 and have a spacegroup
# symbol of R3mH
structures_2 = JarvisStructure.objects.filter(
   formula_full="Mo1 S2",
   density__lt=5,
   spacegroup__symbol="R3mH",
).all()

# You can use to_dataframe() to convert these to a pandas Dataframe object and 
# then view them in Spyder's variable explorer
df_1 = structures_1.to_dataframe()
df_2 = structures_2.to_dataframe()
```

## Advanced Data Manipulation

There are numerous ways to search through your tables, and we've only covered the basics here. 

Advanced users should know that we use [Django's query api](https://docs.djangoproject.com/en/3.2/topics/db/queries/) under the hood. It can take a while to master, so we recommend going through [Django's full tutorial](https://docs.djangoproject.com/en/4.0/) only if you plan on joining our team or are a fully computational student. 

Beginners can simply ask for help. Determining the correct filter can take new users hours, while it will only take our team a minute or two. Save your time and [post questions here](https://github.com/jacksund/simmate/discussions/categories/q-a).