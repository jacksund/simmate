# -*- coding: utf-8 -*-

"""
This is where you add any new database tables. This file is named
"models.py" because that what Django expects! In their terminology, a django 
'model' is the same thing as a 'database table'.

Whenever building new tables, be sure to start from the classes located in our
`simmate.database.base_data_types` module. These let you automatically add useful 
columns and features -- rather than creating everything from scratch. 

For more information and advanced guides, be sure to read through our
[base_data_types documentation](https://jacksund.github.io/simmate/full_guides/database/custom_tables/)
"""

from simmate.database.base_data_types import (
    Calculation,
    DatabaseTable,
    Structure,
    table_column,
)


# Mix-ins let you build out custom tables with common types of data. These will
# automatically build out your table with many different columns. Many
# also have a `from_toolkit` method that makes populating your database super easy
class MyCustomTable1(Structure, Calculation):
    # here, we list out custom columns (so this code is all optional)
    input_01 = table_column.FloatField(null=True, blank=True)
    input_02 = table_column.BooleanField(null=True, blank=True)
    output_01 = table_column.FloatField(null=True, blank=True)
    output_02 = table_column.BooleanField(null=True, blank=True)


# alternatively, we can make a DatabaseTable from scratch that won't be
# used by any workflow.
class MyCustomTable2(DatabaseTable):
    custom_column_01 = table_column.IntegerField()
    custom_column_02 = table_column.FloatField(null=True, blank=True)
