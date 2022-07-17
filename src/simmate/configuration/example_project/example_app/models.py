# -*- coding: utf-8 -*-

"""
This is where you add any new database tables. This file is named
"models.py" because that what Django expects! In their terminology, a django 
model is the same thing as a database table.

Whenever building new tables, be sure to start from the classes located in our
`simmate.database.base_data_types` module. These let you automatically add useful 
columns and features -- rather than creating everything from scratch. 

For more information and advanced guides, be sure to read through our
[base_data_types documentation](https://jacksund.github.io/simmate/simmate/database/base_data_types.html)
"""

from simmate.database.base_data_types import DatabaseTable, Relaxation, table_column


# As an example here, we set up tables for a relaxation. There are two tables
# here: one for the relaxations and a second for storing each ionic step in the
# relaxation. Both of these tables are created automatically with the create_subclasses
# method:
ExampleRelaxation, ExampleIonicStep = Relaxation.create_subclasses(
    "Example",
    module=__name__,  # this line is required
)

# alternatively, we can make a DatabaseTable from scratch
class MyCustomTable(DatabaseTable):
    custom_column_01 = table_column.IntegerField()
    custom_column_02 = table_column.FloatField(null=True, blank=True)
