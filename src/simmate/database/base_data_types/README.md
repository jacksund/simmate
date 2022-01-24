
The Base Data Types
===================

This module defines the fundamental building blocks for storing data. When building new and custom tables, you should inherit from one or more of these classes.


Hierarchy of Types
==================

There are different "levels" of data types define here -- as some types inherit functionality from others.

At the lowest level...

- `base.DatabaseTable` : all tables inherit from this one and it is where common functionality (like the `show_columns` method) is defined

Next are a series of mixins defined in each of these modules...

- `calculation` : holds information about a flow run (corrections, timestamps, etc.)
- `calculation_nested` : a special type of calculation that involves running a workflow made of smaller workflows
- `structure` : holds a periodic crystal structure
- `symmetry` : NOT a mixin. Defines symmetry info for `structure` to reference
- `forces` : holds site forces and lattice stress information
- `thermodynamics` : holds energy and stability information

These mixins are frequently combined in for types of calculations. We define some of those common classes here too:

- `static_energy` : holds a single point energy calculations on a structure
- `relaxation` : holds all steps of a structure geometry optimization


Usage Guide
===========

Creating a custom table involves the following steps:

1. defining your new table's inheritance and custom columns
2. making sure your table is registerd to your database
3. saving data to your new table

All classes in this module are abstract and largely ment to be used as mix-ins. Each class will contain details on it's specific use, but when combining multiple types, you can do the following:

``` python

from simmate.database.base_data_types import (
    table_column,
    Structure,
    Thermodynamics,
)

# Inherit from all the types you'd like to store data on. All of the columns
# define in each of these types will be incorporated into your table.
class MyCustomTable(Structure, Thermodynamics):
    
    # Define the "raw data" for your table. This is required if you'd like to
    # use the to_archive method.
    base_info = (
        [
            "custom_column_01",
            "custom_column_02",
        ]
        + Structure.base_info
        + Thermodynamics.base_info
    )
    
    # Add any custom columns you'd like
    # These follow the types supported by Django.
    
    # This field is required and must be supplied at creation
    custom_column_01 = table_column.IntegerField()

    # This column we say is allowed to be empty. This is often needed if you
    # create an entry to start a calculation and then fill in data after a
    # it completes.
    custom_column_02 = table_column.FloatField(null=True, blank=True)

```

**NOTE:** Unless you are contributing to Simmate's source code, defining a new table does *NOT* automatically register it to your database. To do this, you must follow along with [our tutorial on adding custom workflows](https://github.com/jacksund/simmate/blob/main/tutorials/09_Add_custom_workflows.md).

Once your table is created and registered, you can use the `from_toolkit` method to create and save your data to the database. Note, the information you pass to this method is entirely dependent on what you inherit from and define above.

``` python

from my.example.project import MyCustomTable

new_row = MyCustomTable.from_toolkit(
    # Because we inherited from Structure, we must provide structure
    structure=new_structure,  # provide a ToolkitStructure here
    # 
    # Structures can optionally include a source too.
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

To modify a row, you can load it from your database, update the column, and then resave. Note, there are may more ways to do this, so consult the Django documentation for advanced usage.

``` python

from my.example.project import MyCustomTable

my_row = MyCustomTable.objects.get(id=1)

my_row.custom_column_01 = 4321

my_row.save()
```

Dev Notes
=========

Every base model class has its attributes and methods separated (separated only by comments) into sections. These are simply to organize the code and make it easier to read:

- `Base Info` :
    These fields are the absolute minimum required for the object and can be
    considered the object's raw data.

- `Query-helper Info` :
    These fields aren't required but exist simply to help with common query
    functions. For example, a structure's volume can be calculated using the
    base info fields, but it helps to have this data in a separate column to
    improve common query efficiencies at the cost of a larger database.

- `Relationships` :
    These fields point to other models that contain related data. For example,
    a single structure may be linked to calculations in several other tables.
    The relationship between a structure and it's calculations can be described
    in this section. Note that the code establishing the relationship only exists
    in one of the models -- so we simply add a comment in the other's section.
    TYPES OF RELATIONSHIPS:
        ManyToMany - place field in either but not both
        ManyToOne (ForeignKey) - place field in the many
        OneToOne - place field in the one that has extra features

- `Properties` :
    In a few cases, you may want to add a convience attribute to a model. However,
    in the majority of cases, you'll want to convert the model to some other
    class first which has all of the properties you need. We separate classes
    in this way for performance and clarity. This also allows our core and
    database to be separate and thus modular.

- `Model Methods` :
    These are convience functions added onto the model. For example, it's useful
    to have a method to quickly convert a model Structure (so an object representing
    a row in a database) to a pymatgen Structure (a really powerful python object)

- `For website compatibility` :
    This contains the extra metadata and code needed to get the class to work
    with Django and other models properly.
