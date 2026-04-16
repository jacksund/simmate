# -*- coding: utf-8 -*-

from simmate.website.data_explorer.components import TableComponent

from ..models import EthereumTransaction, EthereumWallet


class EthereumTransactionComponent(TableComponent):
    table = EthereumTransaction
    display_name = "Ethereum Transactions"
    description_short = (
        "Individual ledger entries for activity on the Ethereum blockchain. "
        "This provides a transparent and verifiable record of financial "
        "interactions, such as payments and token transfers."
    )
    template_names = {
        "entries": "ethereum/transactions/table.html",
        "entry": "ethereum/transactions/entry.html",
    }

    enabled_component_types = ["dashboard", "entries", "entry"]
