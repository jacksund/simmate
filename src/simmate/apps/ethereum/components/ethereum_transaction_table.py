# -*- coding: utf-8 -*-

from simmate.website.htmx.components import DynamicTableForm

from ..models import EthereumTransaction, EthereumWallet


class EthereumTransactionTable(DynamicTableForm):
    table = EthereumTransaction
    display_name = "Ethereum Transactions"
    description_short = (
        "Individual ledger entries for activity on the Ethereum blockchain. "
        "This provides a transparent and verifiable record of financial "
        "interactions, such as payments and token transfers."
    )
    template_names = {
        "default": "data_explorer/table_about.html",
        "entries": "ethereum/transactions/table.html",
        "entry": "ethereum/transactions/entry.html",
    }
