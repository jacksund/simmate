# Custom Database Tables Creation

This module offers key components for data storage. When creating new and custom tables, these classes should be inherited.

----------------------------------------------------------------------

## Table Types

Data storage tables range from low-level to high-level. High-level tables inherit basic functionality from low-level tables and the data types stored in them, resulting in tables with enhanced functionality.  

At the lowest level...

- `base.DatabaseTable` : All tables inherit from this base type, which defines common functionality (like the `show_columns` method)

At a higher level, tables inherit the `base.DatabaseTable` to create more specialized tables. These tables contain additional columns specific to the data stored in each. The new columns in each table are created using a feature called a [mixin](https://stackoverflow.com/questions/533631/what-is-a-mixin-and-why-is-it-useful).  These mixins create the following tables:

- `calculation` : Stores information about a specific calculation run (corrections, timestamps, etc.)
- `structure` : Stores a periodic crystal structure
- `symmetry` : NOT a mixin. Defines symmetry relationships for `structure` to reference
- `forces` : Stores site forces and lattice stresses
- `thermodynamics` : Stores energy and stability information
- `density_of_states`: Stores results of a density of states calculation
- `band_structure`: Stores results of a band structure calculation

At the highest level, several lower-level tables can be combined via their mixins. This allows for the creation of tables that can store complex calculations:

- `static_energy` : Stores results of single point energy calculation
- `relaxation` : Stores all steps of a structure geometry optimization
- `nudged_elastic_band` : Stores all results from trajectory calculations
- `dynamics` : Stores all steps of a molecular dynamics simulation
- `calculation_nested` : A special type of calculation that involves running a workflow made of smaller workflows

----------------------------------------------------------------------

## Custom Table Creation

To create a custom table, follow these steps:

1. Define the lower-level tables and data types used to create your new table
2. Register the new table to your database
3. Save data to your new table

All classes in this module are abstract and are primarily used as mix-ins. Each class will contain details on its specific use, but when combining multiple types, you can do the following:

``` python

from simmate.database.base_data_types import (
    table_column,
    Structure,
    Thermodynamics,
)

# Inherit from all the types you'd like to store data on. All of the columns
# defined in each of these types will be incorporated into your table.
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

## Data Loading

Once your table is created and registered, you can use the `from_toolkit` method to create and save your data to the database. Note, the information you pass to this method is entirely dependent on what you inherit from and define above.

``` python

from my.example.project import MyCustomTable

new_row = MyCustomTable.from_toolkit(
    # Because we inherited from Structure, we must provide structure
    structure=new_structure,  // provide a ToolkitStructure here
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

## Column Updating

To modify a row, you can load it from your database, update the column, and then resave. Note, there are many more ways to do this, so consult the Django documentation for advanced usage.

``` python

from my.example.project import MyCustomTable

my_row = MyCustomTable.objects.get(id=1)

my_row.custom_column_01 = 4321

my_row.save()
```

----------------------------------------------------------------------