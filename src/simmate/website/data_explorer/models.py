# -*- coding: utf-8 -*-

from django.db import models as table_column

from simmate.database.core.table import DatabaseTable


class TableCount(DatabaseTable):
    """
    Caches the number of rows for each database table to optimize query times
    on the data explorer homepage.
    """

    table_name = table_column.CharField(max_length=255, unique=True)
    row_count = table_column.IntegerField(default=0)
