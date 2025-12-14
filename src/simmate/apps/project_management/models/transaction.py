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
        "Failed",
        "Under Review",
    ]
    status = table_column.CharField(max_length=30, blank=True, null=True)

    transaction_type_options = [
        "funding",
        "transfer",
        "payment",
        "refund",
        "penalty",
        "admin_adjustment",
    ]
    transaction_type = table_column.CharField(max_length=30, blank=True, null=True)

    funding_options = [
        "Ethereum",
        "Stripe",
        "Venmo",
        "Promotion",
        "Other",
    ]
    transfer_options = [
        "Account Transfer",  # e.g., user switches from github account to gmail one
        "Allowance Distribution",  # e.g., Project transferring to sub-Projects
        "Consolidation",  # e.g., many wallets combining to single one
        "Add Collateral",
        "Remove Collateral",
        "Other",
    ]
    payment_options = [
        "Compute Costs",
        "Compute Earnings",
        "Other",
    ]
    refund_options = [
        "Failed Workflow",
        "Bugged Workflow",
        "Other",
    ]
    penalty_options = [
        "Penalized Worker",
        "Penalized Validator",
        "Penalized User",
        "Banned Account",
        "Other",
    ]
    admin_adjustment_options = [
        "Issue Fix",
        "Other",
    ]
    transaction_subtype = set(
        funding_options
        + transfer_options
        + payment_options
        + penalty_options
        + admin_adjustment_options
    )
    transaction_subtype = table_column.CharField(max_length=30, blank=True, null=True)

    # TODO: link to things like ETH transactoin in source column? Or separate column?

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

    # Note: we use decimal_places=6 to match the USDC precision on ETH
    usdc_amount = table_column.DecimalField(
        max_digits=30,
        decimal_places=6,
        default=0,
    )

    token_amount = table_column.DecimalField(
        max_digits=30,
        decimal_places=6,
        default=0,
    )
    # these have no monetary value and user can edit freely

    collateral_amount = table_column.DecimalField(
        max_digits=30,
        decimal_places=6,
        default=0,
    )
    # This is always an internal transaction (to/from are the same wallet).
    # it simply transfers funds between usdc_amount <-> collateral_amount

    comments = table_column.TextField(blank=True, null=True)
