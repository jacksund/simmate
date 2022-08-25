
# Python Inheritance with Datatables

## Review of concepts

To review key concepts up until this point...

- we setup our database and added calcution results to it.
- we learned about python classes, and in particular, the importance of the `Structure` class.
- we learned how to explore the documentation and use new classes.

Now, we want to bring these ideas together in order to expolore our database. 

## An example table in python

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


## Building tables with inheritance

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

Simmate uses this idea with common materials science data -- such as structures, thermodynamic data, site forces, and more. You'll find our fundamental building blocks for tables in the `simmate.database.base_data_types` module ([here](https://jacksund.github.io/simmate/full_guides/database/custom_tables/))

All of our datatables start from these classes and build up. Up next, we'll look at an actual database table and learn how to use it to view data.

