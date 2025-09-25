# -*- coding: utf-8 -*-

from django.contrib.auth.models import User

from simmate.database.base_data_types import DatabaseTable, table_column

from .wallet import Wallet


class Transaction(DatabaseTable):

    class Meta:
        db_table = "project_management__transactions"

    html_display_name = "Wallet Transactions"
    html_description_short = "The full ledger of wallet transactions"

    status_options = [
        "Pending",
        "Complete",
        "Canceled",
        "Denied",
        "Under Review",
    ]
    status = table_column.CharField(max_length=30, blank=True, null=True)

    transaction_type_options = [
        "funding",
        "transfer",
        "refund",
        "payment",
        "admin_adjustment",
    ]
    transaction_type = table_column.CharField(max_length=30, blank=True, null=True)

    # add a metadata column? or store info in the source?
    # funding_type_options = [
    #     "Ethereum",
    #     "Stripe",
    #     "Venmo",
    #     "Promotion",
    #     "Other",
    # ]
    # payment_type_options = [
    #     "Compute Costs",
    #     "Compute Earnings",
    #     "Other",
    # ]

    sending_user = table_column.ForeignKey(
        User,
        on_delete=table_column.PROTECT,
        related_name="transactions_sent",
        blank=True,
        null=True,
    )
    """
    The user who carried out the transaction. This is needed because...
    1. Projects can have multiple owners + members that can utilize a wallet
    2. Simmate admins may go into a wallet and make a transaction on their behalf
    """

    from_wallet = table_column.ForeignKey(
        Wallet,
        on_delete=table_column.PROTECT,
        related_name="transactions_out",
        blank=True,
        null=True,
    )

    to_wallet = table_column.ForeignKey(
        Wallet,
        on_delete=table_column.PROTECT,
        related_name="transactions_in",
        blank=True,
        null=True,
    )

    usdc_amount = table_column.FloatField(blank=True, null=True)

    token_amount = table_column.FloatField(blank=True, null=True)

    comments = table_column.TextField(blank=True, null=True)
