# Python Inheritance in Datatables

----------------------------------------------------------------------

## Recap of Key Concepts

Before we proceed, let's quickly recap the main concepts we've covered so far...

- [x] We've established our database and populated it with calculation results.
- [x] We've delved into Python classes, focusing on the significance of the `Structure` class.
- [x] We've explored how to navigate documentation and utilize new classes.

Now, we'll integrate these concepts to navigate our database. 

----------------------------------------------------------------------

## Python Table Example

Let's start with the basics... All datatables are represented by a class, and the general format is as follows:

```python
from simmate.database.base_data_types import DatabaseTable, table_column

class MyExampleTable(DatabaseTable):
   column_01 = table_columns.CharField()  # CharField --> text storage
   column_02 = table_columns.BoolField()  # BoolField --> True/False storage
   column_03 = table_columns.FloatField()  # FloatField --> number/decimal storage
```

The corresponding table (populated with random data) would look like this:

| column_01  | column_02 | column_03 |
| ---------- | --------- | --------- |
| jack  | True  | 3.1456  |
| lauren  | False  | 299792458  |
| siona  | True  | 1.6180  |
| scott  | False  | 1.602e-19  |
| ... | ... | ...  |

Creating tables is as simple as defining a class, declaring it as a `DatabaseTable`, and specifying the desired columns.

----------------------------------------------------------------------

## Constructing Tables with Inheritance

However, if we have multiple tables with similar data, this process can become repetitive. For instance, we might want to store structures in various tables, each with columns like density, number of sites, number of elements, etc. To streamline this process, we use Python "inheritance". Here's how it works:

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

| name  | age | height | year | gpa |
| ----- | --- | ------ | ---- | ---|
| jack  | 15  | 6.1  | 2020 | 3.6 |
| lauren | 16  | 5.8  | 2019 | 4.0 |
| siona  | 15  | 5.6  | 2020 | 3.7 |
| scott  | 14  | 6.2  | 2021 | 3.2 |
| ... | ... | ... | ... | ...|

Simmate employs this concept with common materials science data, such as structures, thermodynamic data, site forces, and more. Our fundamental building blocks for tables are found in the `simmate.database.base_data_types` module ([covered here](/full_guides/database/custom_tables/)).

All our datatables are built upon these classes. Next, we'll examine an actual database table and learn how to use it to view data.

----------------------------------------------------------------------