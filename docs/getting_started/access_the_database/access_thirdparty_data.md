
## Accessing third-party data

When running our own calculations with Simmate, it is also important to know what other researchers have already calculated for a given material. Many research teams around the world have built databases made of 100,000+ structures -- and many of these teams even ran calculations on all of them. Here, we will use Simmate to explore their data.

## Loading a table

Let's start with one of the smaller databases out there: [JARVIS](https://jarvis.nist.gov/). It may be smaller than the others, but their dataset still includes ~56,000 structures! Simmate makes the download for all of these under 0.01 GB.

In the previous section, we loaded our `DatabaseTable` from the workflow. But now we don't have a workflow... We just want to grab the table directly. To do this we run the following:

```python
# This line MUST be ran before any tables can be loaded
from simmate.database import connect  # this connects to our database

# This gives the database_table we were using in the previous section
from simmate.database.workflow_results import StaticEnergy

# This loads the table where we store all of the JARVIS data.
from simmate.database.third_parties import JarvisStructure
```

`table` from the previous section and the `MITRelaxation` class here are the exact same class. These are just different ways of loading it. While loading a workflow sets up a database connection for us, we have the do that step manually here (with `from simmate.database import connect`). When loading database tables directly from the `simmate.database` module, the most common error is forgetting to connect to your database. So don't forget to include `from simmate.database import connect`!

## Filling data

Now that we have our datatable class (`JarvisStructure`) loaded, let's check if there's any data in it:

``` python
JarvisStructure.objects.count()
```

!!! note 
    If you accepted the download during the `simmate database reset` command, then you should see that there are thousands of structures already in this database table! 

If the count gives 0, then that means you still need to load data. We can quickly load all of the data using the `load_remote_archive` method. Behind the scenes, this is downloading the JARVIS data from simmate.org and moving it into your database. This can take ~10 minutes because we are actually saving all these structures to your computer -- that way, you can rapidly load these structures in under 1 second in the future.
``` python
# NOTE: This line is only needed if you did NOT accept the download
# when running `simmate database reset`.
JarvisStructure.load_remote_archive()  # This may take ~10min to complete
```

!!! warning
    It is very important that you read the warnings printed by `load_remote_archive`. This data was NOT made by Simmate. We are just helping to distribute it on behalf of these other teams. Be sure to cite them for their work!

Calling `load_remote_archive` loads ALL data to your computer and saves it. This data will not be updated unless you call `load_remote_archive` again. This should only be done every time we release a new archive version (typically once per year). To protect our servers from misuse, you can only call `load_remote_archive()` a few times per month -- no matter what. **Don't overuse this feature.**

## Start exploring the data

Now that we ensured our database if filled with data, we can start looking through:

``` python
# We use [:150] to just show the first 150 rows
data = JarvisStructure.objects.to_dataframe()[:150]
```


Now let's really test out our filtering ability with this new data:
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

## Advanced data manipulation

There are many ways to search through your tables, and we only covered the basics here. Advanced users will benefit from knowing that we use [Django's query api](https://docs.djangoproject.com/en/3.2/topics/db/queries/) under the hood. It can take a long time to master, so we only recommend going through [Django's full tutorial](https://docs.djangoproject.com/en/4.0/) if you plan on joining our team or are a fully computational student. Beginners can just ask for help. Figuring out the correct filter can take new users hours while it will only take our team a minute or two. Save your time and [post questions here](https://github.com/jacksund/simmate/discussions/categories/q-a).

