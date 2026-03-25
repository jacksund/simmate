# -*- coding: utf-8 -*-

from simmate.website.htmx.components import DynamicTableForm

from ..models import EthereumTransaction, EthereumWallet


class EthereumWalletTable(DynamicTableForm):
    table = EthereumWallet
    display_name = "Ethereum Wallets"
    description_short = (
        "Ethereum blockchain addresses used for tracking decentralized "
        "transactions and digital assets. These wallets can be used to manage "
        "project-specific funds and rewards."
    )
    template_names = {
        "default": "data_explorer/table_about.html",
        "entries": "ethereum/wallets/table.html",
        "entry": "ethereum/wallets/entry.html",
    }
