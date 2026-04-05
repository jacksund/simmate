# -*- coding: utf-8 -*-

from simmate.website.data_explorer.components import DynamicTableForm

from ..models import Transaction


class TransactionForm(DynamicTableForm):
    table = Transaction

    template_names = {
        "default": "data_explorer/table_about.html",
        "entries": "project_management/transaction/table.html",
        "entry": "project_management/transaction/view.html",
    }

    display_name = "Wallet Transactions"
    description_short = (
        "A ledger of all financial activity within wallets, including payments, "
        "allocations, and rewards. This provides a full audit trail for all "
        "digital assets."
    )
