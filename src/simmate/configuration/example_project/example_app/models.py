# -*- coding: utf-8 -*-

"""
This is where you add any new database tables. 

This file is named "models.py" because that is what Django expects! In their 
terminology, a django 'model' is the same thing as a 'database table'.

See our online documentation for more information.
"""

from simmate.database.base_data_types import (
    Calculation,
    DatabaseTable,
    Structure,
    table_column,
)


# OPTION 1:
# We can make a DatabaseTable from scratch. This table will only have the
# columns we define, plus a few default ones: id, created_at, update_at, and source
class MyCustomTable1(DatabaseTable):
    custom_column_01 = table_column.IntegerField()
    custom_column_02 = table_column.FloatField(null=True, blank=True)


# OPTION 2:
# Mix-ins let you build out custom tables with common types of data. These will
# automatically build out your table with many different columns. Many
# also have a `from_toolkit` method that makes populating your database super easy
class MyCustomTable2(Structure, Calculation):
    input_01 = table_column.FloatField(null=True, blank=True)
    input_02 = table_column.BooleanField(null=True, blank=True)
    output_01 = table_column.FloatField(null=True, blank=True)
    output_02 = table_column.BooleanField(null=True, blank=True)


# OPTION 3: (advanced users only)
# You can build a table using django instead of simmate
# https://docs.djangoproject.com/
