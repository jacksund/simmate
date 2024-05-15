# Python Inheritance in Datatables

----------------------------------------------------------------------

## Recap of Key Concepts

Before we proceed, let's quickly review the progress we've made so far...

- [x] We established our database at `~/simmate/my_env-database.sqlite`
- [x] We ran a `quantum-espresso` workflow that stored results in our database
- [x] We introduced Python classes, focusing on the significance of the `Structure` class

Next, we'll build on these elements and learn about the database. 

----------------------------------------------------------------------

## A Basic Table

Let's start with the basics: what does the table you saw in DBeaver actually look like in Simmate's Python code?

All datatables are represented by a class, and the general format is as follows:

```python
from simmate.database.base_data_types import DatabaseTable, table_column

class MyExampleTable(DatabaseTable):
   column_01 = table_column.CharField()  # CharField --> text storage
   column_02 = table_column.BoolField()  # BoolField --> True/False storage
   column_03 = table_column.FloatField()  # FloatField --> number/decimal storage
```

The corresponding table (populated with random data) would look like this:

| column_01 | column_02 | column_03 |
| --------- | --------- | --------- |
| jack      | True      | 3.1456    |
| lauren    | False     | 299792458 |
| siona     | True      | 1.6180    |
| scott     | False     | 1.602e-19 |
| ...       | ...       | ...       |

Creating tables is as simple as defining a class, declaring it as a `DatabaseTable`, and specifying the desired columns with `table_column`.

----------------------------------------------------------------------

## A Table with Inheritance

However, if we have multiple tables with similar data, this process can become repetitive. For instance, we might want to store structures in various tables, each with columns like density, number of sites, number of elements, etc. To streamline this process, we use Python "inheritance". Here's how it works...

First, we define a table with common data (let's use `Person` as an example).

```python
from simmate.database.base_data_types import DatabaseTable, table_column

class Person(DatabaseTable):
   name = table_columns.CharField()
   age = table_columns.IntField()
   height = table_columns.FloatField()
```

Next, we create a separate table that includes this data and more:

```python
class Student(Person):  # <--- note we have Person here instead of DatabaseTable
   year = table_columns.IntField()  # e.g. class of 2020
   gpa = table_columns.FloatField()
```

The `Student` datatable now looks like this:

| name   | age | height | year | gpa |
| ------ | --- | ------ | ---- | --- |
| jack   | 15  | 6.1    | 2020 | 3.6 |
| lauren | 16  | 5.8    | 2019 | 4.0 |
| siona  | 15  | 5.6    | 2020 | 3.7 |
| scott  | 14  | 6.2    | 2021 | 3.2 |
| ...    | ... | ...    | ...  | ... |

Note that the `Student` table includes both our newly defined columns (`year` + `gpa`) as well as all of the columns from `Person` (`name`, `age`, `height`). This is because `Student` inherits from `Person`.

----------------------------------------------------------------------

## A full example in Simmate

Simmate uses this concept of inheritance with common materials science data. This includes tables for structures, thermodynamic data, site forces, and more.

Let's use the `workflows_staticenergy` table as an example. Open this table in DBeaver, and take a closer look at all of the columns. This table inherits from several others:

- `Structure`
- `Thermodynamics`
- `Forces`
- `Calculation`

This is because the calculation involves the following information, respectively:

- an input structure *(formula, num_sites, density, etc.)*
- thermodynamic data *(final energy, energy per atom, stability, etc.)*
- site forces and lattice stress *(available because we used DFT to calculate the energy)*
- general calculation info *(e.g. calculation time, workflow name, dirctory name, etc.)*

This builds out the massive table for us. Then, during analysis, you can go in and select which columns you actually are interested in from the many available.

!!! tip
    Experienced python users: take a look at our source code for the `StaticEnergy` table [here](https://github.com/jacksund/simmate/blob/main/src/simmate/database/base_data_types/static_energy.py). You'll see we just provide these data types as mix-ins.


!!! warning
    Do not confuse the database table `Structure` with the toolkit `Structure`. One represents structural data in a table, while the other helps with advanced analysis and manipulation of a structure. You can use the aliases `DatabaseStructure` and `ToolkitStructure` to help keep them separate if you wish.
    
    Note also, you can convert a `ToolkitStructure` into a single row for a `DatabaseStructure`. Simmate does this frequently behind the scenes in order to save information to your database.

----------------------------------------------------------------------