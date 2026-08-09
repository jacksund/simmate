# -*- coding: utf-8 -*-

from django.contrib.auth.models import User

from simmate.database.core import DatabaseTable, table_column

from .container import Container


class UsageLog(DatabaseTable):

    class Meta:
        db_table = "inventory_management__usage_logs"

    # -------------------------------------------------------------------------

    container = table_column.ForeignKey(
        Container,
        on_delete=table_column.CASCADE,
        null=True,
        blank=True,
        related_name="usage_logs",
    )

    user = table_column.ForeignKey(
        User,
        on_delete=table_column.PROTECT,
        null=True,
        blank=True,
        related_name="usage_logs",
    )

    amount_removed = table_column.DecimalField(
        max_digits=10,
        decimal_places=3,
    )

    comments = table_column.TextField(
        blank=True,
        null=True,
    )

    # -------------------------------------------------------------------------

    # TODO: link to a Project object
    # project = ...

    # TODO: add downstream child batch/containers?
