# -*- coding: utf-8 -*-

from simmate.website.htmx.components import DynamicTableForm

from .models import EthereumWallet, EthereumTransaction


class EthereumWalletTable(DynamicTableForm):
    table = EthereumWallet
    html_display_name = "Ethereum Wallets"
    html_description_short = (
        "Ethereum blockchain addresses used for tracking decentralized "
        "transactions and digital assets. These wallets can be used to manage "
        "project-specific funds and rewards."
    )
    template_names = {
        "default": "data_explorer/table_about.html",
        "entries": "ethereum/wallets/table.html",
        "entry": "ethereum/wallets/entry.html",
    }


class EthereumTransactionTable(DynamicTableForm):
    table = EthereumTransaction
    html_display_name = "Ethereum Transactions"
    html_description_short = (
        "Individual ledger entries for activity on the Ethereum blockchain. "
        "This provides a transparent and verifiable record of financial "
        "interactions, such as payments and token transfers."
    )
    template_names = {
        "default": "data_explorer/table_about.html",
        "entries": "ethereum/transactions/table.html",
        "entry": "ethereum/transactions/entry.html",
    }
