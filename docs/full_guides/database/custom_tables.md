
# Building custom database tables

This module defines the fundamental building blocks for storing data. When building new and custom tables, you should inherit from one or more of these classes.

----------------------------------------------------------------------

## Table Types

The tables that store data can be classified from low-level to high-level. High-level tables inherit basic functionality from low-level tables and from the data types that are stored in that table to create tables with enhanced functionality.  

At the lowest level...

- `base.DatabaseTable` : all tables inherit from this base type and this is where common functionality (like the `show_columns` method) is defined

At a higher level, tables inherit the `base.DatabaseTable` to create a series of more specialized tables. These tables contain additional columns that are specific to the kinds of data stored in each. The new columns in each table are created using a special feature called a [mixin](https://stackoverflow.com/questions/533631/what-is-a-mixin-and-why-is-it-useful).  These mixins create the following tables:

- `calculation` : holds information about a specific calculation run (corrections, timestamps, etc.)
- `structure` : holds a periodic crystal structure
- `symmetry` : NOT a mixin. Defines symmetry relationships for `structure` to reference
- `forces` : holds site forces and lattice stresses
- `thermodynamics` : holds energy and stability information
- `density_of_states`: holds results of a density of states calculation
- `band_structure`: holds results of a band structure calculation

At an even higher level, we can combine several lower-level tables via their mixins. This allows us to easily create tables that can store complex calculations:

- `static_energy` : holds results of single point energy calculation
- `relaxation` : holds all steps of a structure geometry optimization
- `nudged_elastic_band` : holds all results from trajectory calculations
- `dynamics` : holds all steps of a molecular dynamics simmulation
- `calculation_nested` : a special type of calculation that involves running a workflow made of smaller workflows

----------------------------------------------------------------------

## Building an example table

Creating a custom table involves the following steps:

1. defining the lower-level tables and data types used to create your new table
2. registering the new table to your database
3. saving data to your new table

All classes in this module are abstract and largely meant to be used as mix-ins. Each class will contain details on its specific use, but when combining multiple types, you can do the following:

``` python

from simmate.database.base_data_types import (
    table_column,
    Structure,
    Thermodynamics,
)

# Inherit from all the types you'd like to store data on. All of the columns
# define in each of these types will be incorporated into your table.
class MyCustomTable(Structure, Thermodynamics):
    
    # ----- Table columns -----
    
    # Add any custom columns you'd like.
    # These follow the types supported by Django.
    
    # This custom field will be required and must be supplied at creation
    custom_column_01 = table_column.IntegerField()

    # This column we say is allowed to be empty. This is often needed if you
    # create an entry to start a calculation and then fill in data after a
    # it completes.
    custom_column_02 = table_column.FloatField(null=True, blank=True)

    # ----- Extra features -----

    # If you are not using the `Calculation` mix-in, you'll have to specify
    # which app this table is associated with. To determine what you set here,
    # you should have completed the advanced simmate tutorials (08-09).
    class Meta:
        app_label = "my_custom_app"
    
    # (OPTIONAL) Define the "raw data" for your table. This is required if 
    # you'd like to use the `to_archive` method. Fields from the mix-in 
    # will automatically be added.
    archive_fields = [
        "custom_column_01",
        "custom_column_02",
    ]
    
    # (OPTIONAL) Define how you would like data to be accessible in the REST 
    # API from the website server.
    api_filters = {
        "custom_column_01": ["range"],
        "custom_column_02": ["range"],
    }

```

!!! warning
    Unless you are contributing to Simmate's source code, defining a new table does *NOT* automatically register it to your database. To do this, you must follow along with [our custom workflows guides](/full_guides/workflows/creating_new_workflows/).

----------------------------------------------------------------------

## Loading data

Once your table is created and registered, you can use the `from_toolkit` method to create and save your data to the database. Note, the information you pass to this method is entirely dependent on what you inherit from and define above.

``` python

from my.example.project import MyCustomTable

new_row = MyCustomTable.from_toolkit(
    # Because we inherited from Structure, we must provide structure
    structure=new_structure,  # provide a ToolkitStructure here
    # 
    # All tables can optionally include a source too.
    source="made by jacksund",
    #
    # Because we inherited from Thermodynamics, we must provide energy
    energy=-5.432,
    #
    # Our custom fields can also be added
    custom_column_01=1234,
    custom_column_02=3.14159,
)

new_row.save()
```

----------------------------------------------------------------------

## Updating a column

To modify a row, you can load it from your database, update the column, and then resave. Note, there are may more ways to do this, so consult the Django documentation for advanced usage.

``` python

from my.example.project import MyCustomTable

my_row = MyCustomTable.objects.get(id=1)

my_row.custom_column_01 = 4321

my_row.save()
```

----------------------------------------------------------------------
