# -*- coding: utf-8 -*-

from django.contrib.auth.models import User

from simmate.database.base_data_types import DatabaseTable, table_column

from .project import Project


class Wallet(DatabaseTable):

    class Meta:
        db_table = "project_management__wallets"

    html_display_name = "Wallets"
    html_description_short = (
        "Digital accounts that contain USDC or Token assets for budgeting and spending."
    )

    source = None  # disable col

    wallet_type_options = [
        "project",
        "user",
        # unique types where only one exists for each:
        "simmate-escrow",
        "simmate-treasury",
        "validator-pool",
    ]
    wallet_type = table_column.CharField(max_length=30, blank=True, null=True)
    """
    Whether the wallet is owned by a specific user or project.
    """

    user = table_column.OneToOneField(
        User,
        on_delete=table_column.PROTECT,
        related_name="wallet",
        blank=True,
        null=True,
    )

    project = table_column.OneToOneField(
        Project,
        on_delete=table_column.PROTECT,
        related_name="wallet",
        blank=True,
        null=True,
    )

    usdc_balance = table_column.DecimalField(decimal_places=6, default=0)

    token_balance = table_column.DecimalField(decimal_places=6, default=0)

    # only for workers & validators
    collateral_balance = table_column.DecimalField(decimal_places=6, default=0)
