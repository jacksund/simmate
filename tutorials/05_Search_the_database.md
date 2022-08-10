# Search the database

In this tutorial, you will learn how to explore your database as well as load data from third-party providers. Beginners will also be introduced to python inheritance.

1. [The quick tutorial](#the-quick-tutorial)
2. [The full tutorial](#the-full-tutorial)
    - [Python Inheritance with Datatables](#python-inheritance-with-datatables)
    - [Accessing results from local calculations](#accessing-results-from-local-calculations)
    - [Accessing third-party data](#accessing-third-party-data)

<br/><br/>

# The quick tutorial

1. Make sure you've initialized your database. This was done in tutorial 2 with the command `simmate database reset`. Do NOT rerun this command as it will empty your database and delete your results.
2. Go to the `simmate.database` module to view all available tables.
3. The table for Tutorial 2's results are located in the `StaticEnergy` datatable class, which can be loaded via either of these options:
```python
# OPTION 1
from simmate.database import connect # this connects to our database
from simmate.database.workflow_results import StaticEnergy

# OPTION 2 (slower but recommended for convenience)
from simmate.workflows.utilities import get_workflow
workflow = get_workflow("static-energy.vasp.mit")
table = workflow.database_table  # results here is the same thing as StaticEnergy above
```
4. View all the possible table columns with `StaticEnergy.show_columns()`
5. View the full table as pandas dataframe with `StaticEnergy.objects.to_dataframe()`
6. Filter results using [django-based queries](https://docs.djangoproject.com/en/4.0/topics/db/queries/). For example:
```python
filtered_results = StaticEnergy.objects.filter(formula_reduced="NaCl", nsites__lte=2).all()
```
7. Convert the final structure from a database object (aka `DatabaseStructure`) to a structure object (aka `ToolkitStructure`).
```python
single_relaxation = StaticEnergy.objects.filter(formula_reduced="NaCl", nsites__lte=2).first()
nacl_structure = single_relaxation.to_toolkit()
```
8. For third-party data (like [Material Project](https://materialsproject.org/), [AFLOW](http://aflowlib.org/), [COD](http://www.crystallography.net/cod/), etc.) load the database table and (if you are NOT using a prebuilt database) then request to download all the available data:
```python
from simmate.database import connect  # this connects to our database
from simmate.database.third_parties import JarvisStructure

# NOTE: This line is only needed if you did NOT accept the download
# when running `simmate database reset`.
# This only needs to ran once -- then data is stored locally.
JarvisStructure.load_remote_archive()

# now explore the data (only the first 150 structures here)
first_150_rows = JarvisStructure.objects.all()[:150]
dataframe = first_150_rows.to_dataframe()
```
> :warning: To protect our servers, you can only call `load_remote_archive()` a few times per month. Don't overuse this feature.

<br/><br/>

# The full tutorial

> :bulb: This entire tutorial should be ran on your local computer because we will be using Spyder. To use results from your remote calculations, you can copy/paste your database file from your remote computer to where our local database one should be (~/simmate/my_env-database.sqlite3). Note, copy/pasting will no longer be necessary when we switch to a cloud database in the next tutorial.

<br/>

## Python Inheritance with Datatables

To review key concepts up until this point...
- In tutorial 2, we setup our database and added calcution results to it.
- In tutorials 3, we learned about python classes, and in particular, the importance of the `Structure` class.
- In tutorial 4, we learned how to explore the documentation and use new classes.

Now, we want to bring these ideas together in order to expolore our database. 

Let's start simple... All datatables are represented by a class, where the general format looks like this:

```python
from simmate.database.base_data_types import DatabaseTable, table_column

class MyExampleTable(DatabaseTable):
   column_01 = table_columns.CharField()  # CharField --> means we store text
   column_02 = table_columns.BoolField()  # BoolField --> means we store True/False
   column_03 = table_columns.FloatField()  # FloatField --> means we store a number/decimal
```

And the corresponding table (with random data added) would look like...

| column_01  | column_02 | column_03 |
| ---------- | --------- | --------- |
| jack  | True  | 3.1456  |
| lauren  | False  | 299792458  |
| siona  | True  | 1.6180  |
| scott  | False  | 1.602e-19  |
| ... | ... | ...  |

That's how all tables are made! We just make a class, say it is a `DatabaseTable` and then list off our desired columns.

However, this could get really repetitive if we have a bunch of tables that contain similar information. For example, we may want to store structures in many different tables -- each one with columns like density, number of sites, number of elements, etc.. To save time, we use what is known as python "inheritance". Here's how it works:

First, we define a table with common information (let's say a `Person`).

```python
from simmate.database.base_data_types import DatabaseTable, table_column

class Person(DatabaseTable):
   name = table_columns.CharField()
   age = table_columns.IntField()
   height = table_columns.FloatField()
```

Next, we want a separate table to contain this type of information and more:

```python
class Student(Person):  # <--- note we have Person here instead of DatabaseTable
   year = table_columns.IntField()  # e.g. class of 2020
   gpa = table_columns.FloatField()
```

The `Student` datatable now looks like this:

| name  | age | height | year | gpa |
| ----- | --- | ------ | ---- | ---|
| jack  | 15  | 6.1  | 2020 | 3.6 |
| lauren | 16  | 5.8  | 2019 | 4.0 |
| siona  | 15  | 5.6  | 2020 | 3.7 |
| scott  | 14  | 6.2  | 2021 | 3.2 |
| ... | ... | ... | ... | ...|

Simmate uses this idea with common materials science data -- such as structures, thermodynamic data, site forces, and more. You'll find our fundamental building blocks for tables in the `simmate.database.base_data_types` module ([here](https://github.com/jacksund/simmate/tree/main/src/simmate/database/base_data_types))

All of our datatables start from these classes and build up. Up next, we'll look at an actual database table and learn how to use it to view data.

<br/>

## Accessing results from local calculations

In Tutorial 2, we ran a calculation and then added results to our database table. Here, we will now go through the results. 

We know our workflow's name was `energy-mit`, so let's start by grabbing that workflow again. The database table for results is always attached to the workflow as the `database_table` attribute. You can load it like this:

```python
from simmate.workflows.utilities import get_workflow
workflow = get_workflow("static-energy.vasp.mit")
table = workflow.database_table
```

To see all of the data this table stores, we can use it's `show_columns()` method. Here, we'll see a bunch of columns printed for us...

```python
table.show_columns()
```

... which will output ...

```
- id
- created_at
- updated_at
- source
- structure_string
- nsites
- nelements
- elements
- chemical_system
- density
- density_atomic
- volume
- volume_molar
- formula_full
- formula_reduced
- formula_anonymous
- spacegroup (relation to Spacegroup)
- workflow_name
- location
- directory
- run_id
- corrections
- site_forces
- lattice_stress
- site_force_norm_max
- site_forces_norm
- site_forces_norm_per_atom
- lattice_stress_norm
- lattice_stress_norm_per_atom
- energy
- energy_per_atom
- energy_above_hull
- is_stable
- decomposes_to
- formation_energy
- formation_energy_per_atom
- band_gap
- is_gap_direct
- energy_fermi
- conduction_band_minimum
- valence_band_maximum
```

These are a lot of columns... and you may not need all of them. But Simmate still builds all of these for you right away because they don't take up very much storage space.

Next we'd want to see the table with all of its data. To access the table rows, we use the `objects` attribute, and then to get this into a table, we convert to a "dataframe". A dataframe is a filtered portion of a database table -- and because we didn't filter any of our results yet, our dataframe is just the whole table. 

```python
data = table.objects.to_dataframe()
```
Open up this variable by double-clicking `data` in Spyder's variable explorer (top right window) and you can view the table. Here's what a typical dataframe looks like in Spyder:

<!-- This is an image of an Pandas Dataframe in Spyder -->
<p align="center" style="margin-bottom:40px;">
<img src="https://www.spyder-ide.org/blog/spyder-variable-explorer/table-headings.png"  height=330 style="max-height: 330px;">
</p>

Next, we can use our table columns to start filtering through our results. Your search results will be given back as a list of rows that met the filtering criteria. In the example above, we converted that list of results to into a dataframe for easy viewing. You can also convert each row into our `ToolkitStructure` from tutorial 3! There are a bunch of things to try, so play around with each:

```python

# We can filter off rows in the table. Any column can be used!
search_results = table.objects.filter(
    formula_reduced="NaCl",  # check an exact match for any column
    nelements=2,  # filter a column based on a greater or equal to (gte) condition
).all()

# If we look at this closely, you notice this is just a list of database objects (1 object = 1 row)
print(search_results)

# We can convert this list of objects to a dataframe like we did above
data = search_results.to_dataframe()

# Or we can convert to a list of structure objects (ToolkitStructure)
structures = search_results.to_toolkit()
```

This isn't very exciting now because we just have one row/structure in our table :cry:, but we'll do some more exciting filtering in the next section.

<br/>

## Accessing third-party data

When running our own calculations with Simmate, it is also important to know what other researchers have already calculated for a given material. Many research teams around the world have built databases made of 100,000+ structures -- and many of these teams even ran calculations on all of them. Here, we will use Simmate to explore their data.

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

Now that we have our datatable class (`JarvisStructure`) loaded, let's check if there's any data in it:

``` python
JarvisStructure.objects.count()
```

If you are accepted the download during the `simmate database reset` command, then you should see that there are thousands of structures already in this database table! 

However, if the count gives 0, then that means you still need to load data.We can quickly load all of the data using the `load_remote_archive` method. Behind the scenes, this is downloading the JARVIS data from simmate.org/downloads and moving it into your database. This can take ~10 minutes because we are actually saving all these structures to your computer -- that way, you can rapidly load these structures in under 1 second in the future.
``` python
# NOTE: This line is only needed if you did NOT accept the download
# when running `simmate database reset`.
JarvisStructure.load_remote_archive()  # This may take ~10min to complete
```

> :warning: It is very important that you read the warnings printed by `load_remote_archive`. This data was NOT made by Simmate. We are just helping to distribute it on behalf of these other teams. Be sure to cite them for their work!

Calling `load_remote_archive` loads ALL data to your computer and saves it. This data will not be updated unless you call `load_remote_archive` again. This should only be done every time we release a new archive version (typically once per year). To protect our servers from misuse, you can only call `load_remote_archive()` a few times per month -- no matter what. **Don't overuse this feature.**

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

There are many ways to search through your tables, and we only covered the basics here. Advanced users will benefit from knowing that we use [Django's query api](https://docs.djangoproject.com/en/3.2/topics/db/queries/) under the hood. It can take a long time to master, so we only recommend going through [Django's full tutorial](https://docs.djangoproject.com/en/4.0/) if you plan on joining our team or are a fully computational student. Beginners can just ask for help. Figuring out the correct filter can take new users hours while it will only take our team a minute or two. Save your time and [post questions here](https://github.com/jacksund/simmate/discussions/categories/q-a).

When you're ready, you can advance to [the next tutorial](https://github.com/jacksund/simmate/blob/main/tutorials/06_Building_custom_workflows), which can be completed on your local computer.
