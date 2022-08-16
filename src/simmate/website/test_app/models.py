# -*- coding: utf-8 -*-

from simmate.database.base_data_types import (
    Calculation,
    DatabaseTable,
    Forces,
    Structure,
    Thermodynamics,
    table_column,
)


class TestDatabaseTable(DatabaseTable):

    base_info = ["column1", "column2"]

    column1 = table_column.BooleanField()
    column2 = table_column.FloatField()

    class Meta:
        app_label = "test_app"


class TestStructure(Structure):
    pass


class TestCalculation(Calculation):
    pass


# Forces is always used with the Structure mix-in
class TestForces(Structure, Forces):
    pass


# We add the Structure mixin in order to test the "update stabilites" methods
class TestThermodynamics(Structure, Thermodynamics):
    pass
