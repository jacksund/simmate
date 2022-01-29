# -*- coding: utf-8 -*-

from simmate.database.base_data_types import (
    DatabaseTable,
    table_column,
    Spacegroup,
    Structure,
    Calculation,
    Forces,
    Thermodynamics,
    StaticEnergy,
    Relaxation,
    NestedCalculation,
)


class TestDatabaseTable(DatabaseTable):

    base_info = ["column1", "column2"]

    column1 = table_column.BooleanField()
    column2 = table_column.FloatField()

    class Meta:
        app_label = "test_app"


TestDatabaseTable2 = TestDatabaseTable.create_subclass(
    name="TestDatabaseTable2",
    module=__name__,  # required for serialization
    new_column3=table_column.BooleanField(),
)
