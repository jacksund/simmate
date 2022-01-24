
Overview
=========

_**WARNING:**_ This module is only for the Simmate dev team or third-party contributors that want to add their own data! Users should instead use the `load_remote_archive` method to access data. See the [tutorial on accessing the database](https://github.com/jacksund/simmate/blob/main/tutorials/05_Search_the_database.md).

This module is for pulling data from various databases into Simmate using third-party codes. This can then be used to build archives that users may access.

Adding a new provider
=====================

**Note, if you want to avoid this guide, you can just contact our team! [Open a github issue](https://github.com/jacksund/simmate/issues) to get our attention. In most cases, we only need a CSV or JSON file of your data (in any data format you'd like), and we can handle the rest for you. If you'd like to contribute the data on your own, keep reading!**


The end goal for each provider is to allow a user do the following:
``` python
from simmate.shortcuts import setup  # connects to database

from simmate.third_parties import ExampleProviderData

ExampleProviderData.load_remote_archive()

search_results = ExampleProviderData.objects.filter(...).all()
# plus all to_dataframe / to_toolkit features discussed elsewhere
```

The key part that providers must understand is the `load_remote_archive` method. This method does the following:

1. loads an archive of available data (as a `zip` file from some CDN)
2. unpacks the data into the Simmate format
3. saves everything to the user's database (by defualt this is `~/simmate/database.sqlite3`).

**This guide serves to make the first step work!** Specifically, providers must make the archive that `load_remote_archive` will load in step 1 and make it downloadable by a CDN or API endpoint. It is up to the provider whether they personally distribute the archive or allow Simmate to distribute it for them.

To illustrate how this is done, we will walk through the required steps:

1. Define a Simmate table
2. Download data into the Simmate format (i.e. populate the Simmate table)
3. Compress the data to archive file
4. Make the archive available via a CDN
5. Link the CDN to the Simmate table

Note, these steps involve contributing changes to Simmate's code, so we recommend [opening a github issue](https://github.com/jacksund/simmate/issues) before starting too. That way, our team can help you through this process. If you are new to Github and contributing, be sure to read our [tutorial for contributors](https://github.com/jacksund/simmate/tree/main/tutorials/Guides_for_contributors) too.


Step 1: Define a Simmate table
------------------------------

To host data, Simmate must first know what kind of data you are going to host. We do this by adding a new file to the `simmate.database.third_party` module. You can view this folder on github [here](https://github.com/jacksund/simmate/tree/main/src/simmate/database/third_parties).

Start by defining a `DatabaseTable` with any custom columns / database mix-ins. You can scroll through the other providers to see how tables are made. Good examples to view are for [JARVIS](https://github.com/jacksund/simmate/blob/main/src/simmate/database/third_parties/jarvis.py) and [Materials Project](https://github.com/jacksund/simmate/blob/main/src/simmate/database/third_parties/materials_project.py).

Here is a template with useful comments to get you started:

``` python

# Start by deciding which base data types you can include. Here, we include a
# crystal structure and an energy, so we use the Structure and Thermodynamics
# mix-ins.
from simmate.database.base_data_types import (
    table_column, 
    Structure, 
    Thermodynamics,
)

class ExampleProviderData(Structure, Thermodynamics):
    
    # This Meta class tells Simmate where to store the table within our database.
    # All providers with have the exact same thing here. 
    class Meta:
        app_label = "third_parties"

    # This attribute tells Simmate what the "raw data" is. All table columns
    # can be recreated using the data here.
    base_info = [
        "id", # required
        "structure_string", # required for Structure mix-in
        "energy",  # required for Thermodynamics mix-in
        "custom_column_01",
        "custom_column_02",
    ]

    # By default, the ID column is an IntegerField, but if your data uses a string
    # like "mp-1234" to denote structures, you can update this column to
    # accept a string instead.
    id = table_column.CharField(max_length=25, primary_key=True)

    # Write the name of your team here!
    source = "The Example Provider Project"

    # If you have any custom fields that you'd like to add, list them off here.
    # All data types supported by Django are also supported by Simmate. You can
    # view those options here:
    #   https://docs.djangoproject.com/en/4.0/ref/models/fields/
    custom_column_01 = table_column.FloatField(blank=True, null=True)
    custom_column_02 = table_column.BooleanField(blank=True, null=True)
    
    # Leave this as None for now. We will update this attribute in a later step.
    remote_archive_link = None
    
    # (OPTIONAL) if you host your data on a separate website, you can specify 
    # how to access that structure here. This is important if you want users
    # to switch to your site for aquiring additional data. 
    @property
    def external_link(self) -> str:
        return f"https://www.exampleprovider.com/structure/{self.id}"

```

Before moving on, make sure your table was configured properly by doing the following:

``` bash
# in the command line
simmate database reset
```

``` python
# in python

from simmate.shortcuts import setup  # connects to database

from simmate.third_parties import ExampleProviderData

# This will show you all the columns for your table
ExampleProviderData.show_columns()

# this will show you exactly what the table looks like
my_table = ExampleProviderData.objects.to_dataframe()
```


Step 2: Download data into the Simmate format
----------------------------------------------

Now that Simmate knows what to expect, we can load your data into the database. This can be done in serveral ways. It is entirely up to you which method to use, but here are our recommended options:

1. **JSON or CSV file.** If all of your data can be provide via a dump file, then we can use that! This is typically the easiest for a provider's server. For an example of this, see the COD implementation, which uses a download of CIF files.

2. **A custom python package.** Feel free to add an optional dependency if your team has already put a lot of work into loading data using a python package. A great example of this is the MPRester class in pymatgen, which we use to pull Material Project data. (JARVIS, AFLOW, OQMD currently use this option too).

3. **REST API or GraphQL.** If you have a web API, we can easily pull data using the python `requests` package. Note, in many cases, a REST API is an inefficient way to pull data - as it involves querying a database thousands of times (once for each page of structures) -- potentially crashing the server. In cases like that, we actually prefer a download file (option 1, shown above).

4. **OPTIMADE endpoint.** This is a standardized REST API endpoint that many databases are using now. The huge upside here is that each database will have a matching API -- so once your team has an OPTIMADE endpoint, we can pull data into Simmate with ease. There's no need to build a 2nd implementation. The downside is the same as option 3: OPTIMADE doesn't have a good way to pull data in bulk. Their team is [currently working on this though](https://github.com/Materials-Consortia/OPTIMADE/issues/364).

5. **Web scraping.** As an absolute last resort, we can use `requests` to scrape webpages for data (or `selenium` in even more extreme cases.). This requires the most work from our team and is also the least efficient way to grab data. Therefore, scraping should always be avoided if possible.

With your data in hand, you will now add a file that saves data to the local simmate database on your computer. This file can be added to the `for_providers` module ([here](https://github.com/jacksund/simmate/tree/main/src/simmate/database/third_parties/for_providers)). However, if you want your data and it's access to remain private, you can also keep this file out of Simmate's source-code. It's up to you, but we encourage providers to host their file in the Simmate repo -- so we can give feedback and so future providers can use it as an example/guide. 

Either way, here is a template of how that file will look like:

``` python

from django.db import transaction

from tqdm import tqdm
from pymatgen.core.structure import Structure

from simmate.database.third_parties import ExampleProviderData

# If you want to use a custom package to load your data, be sure to let our team
# know how to install it.
try:
    from my_package.db import get_my_data
except:
    raise ModuleNotFoundError(
        "You must install my_package with `conda install -c conda-forge my_package`"
    )


# We make this an "atomic transaction", which means if any error is encountered
# while saving results to the database, then the database will be reset to it's
# original state.
@transaction.atomic
def load_all_structures():

    # Use whichever method you chose above to load all of your data!
    # Here' we are pretending to use a function that loads all data into a 
    # python dictionary, but this can vary.
    data = get_my_data()

    # Now iterate through all the data -- which is a list of dictionaries.
    # We use tqdm() to monitor progress.
    for entry in tqdm(data):

        # The structure is in the atoms field as a dictionary. We pull this data
        # out and convert it to a pymatgen Structure object.
        structure = Structure(
            lattice=entry["atoms"]["lattice_mat"],
            species=entry["atoms"]["elements"],
            coords=entry["atoms"]["coords"],
            coords_are_cartesian=entry["atoms"]["cartesian"],
        )

        # Now that we have a pymatgen structure object, we can feed that and all
        # other data to the from_toolkit() method. This will create a database
        # object in the Simmate format. Note the data we pass here is based on
        # the ExampleProviderData we defined in the other file.
        structure_db = ExampleProviderData.from_toolkit(
            id=entry["my_id"],
            structure=structure,  # required by Structure mix-in
            energy=entry["my_final_energy"],  # required by Thermodynamics mix-in
            custom_column_01=entry["my_custom_column_01"],
            # The get method is useful if not all entries have a given field.
            custom_column_02=entry.get("my_custom_column_02"),
        )

        # and save it to our database!
        structure_db.save()

```

Try running this on your dataset (or a subset of data if you want to quickly test things). When it finishes, you can ensure data was loaded properly by running:

``` python
# in python

from simmate.shortcuts import setup  # connects to database

from simmate.third_parties import ExampleProviderData

# Check that the number of rows matches your source data.
total_entries = ExampleProviderData.objects.count()

# View the data!
# The [:100] limits this to your first 100 results
my_table = ExampleProviderData.objects.to_dataframe()[:100]
```

And that's it for writing new code! All that's left is making your data available for others.


Step 3: Compress the data to archive file
-----------------------------------------

This will be the easiest step yet. We need to make a `zip` file for users to download, which can be done in one line:

``` python
ExampleProviderData.objects.to_archive()
```

You'll find a file named `ExampleProviderData.zip` in your working directory. You can practice reloading this data into your database too:

1. Make a copy of your database file in `~/simmate/` so you don't lose your work
2. In the terminal, reset your database with `simmate database reset`
3. In python, try reloading your data with `ExampleProviderData.load_archive()`
4. Try viewing your data again with `ExampleProviderData.objects.to_dataframe()`


Step 4: Make the archive available via a CDN
--------------------------------------------

Users with now need the archive file you made to access your data. So you must decide: how should this `zip` file be downloaded by users? 

If you give Simmate approval, we can host your archive file on our own servers. Otherwise you must host your own. The only requirement for your host server is that the `zip` file can be downloaded from a URL.

While we encourage open-source databases, if you consider your dataset private or commercial, Simmate does not require any payment or involvement for how this CDN is hosted and maintained. Thus, you can manage access to this URL via a subscription or any other method. However, Simmate's CDNs are reserved for archives that are freely distributed.


Step 5: Link the CDN to the Simmate table
-----------------------------------------

In Step 1, we left one attribute as None in our code: `remote_archive_link`. As a final step, you need to take the URL that you're host your `zip` file at and paste it here. For example, that line will become:

``` python
remote_archive_link = "https://simmate.org/archives/ExampleProviderData.zip"
```

That's it! Let's test out everything again. Note, we are now using `load_remote_archive` in this process -- which will load your `zip` file from the URL.

1. Make a copy of your database file in `~/simmate/` so you don't lose your work
2. In the terminal, reset your database with `simmate database reset`
3. In python, try reloading your data with `ExampleProviderData.load_remote_archive()`
4. Try viewing your data again with `ExampleProviderData.objects.to_dataframe()`

If you've made it this far, thank you for contributing!!! Your data is now easily accessible to all Simmate users, which we hope facilitates its use and even lessen the load on your own servers. Congrats!
