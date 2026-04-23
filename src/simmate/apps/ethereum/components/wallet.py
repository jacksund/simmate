# -*- coding: utf-8 -*-

from simmate.website.data_explorer.components import TableComponent

from ..models import EthereumTransaction, EthereumWallet


class EthereumWalletComponent(TableComponent):
    table = EthereumWallet
    display_name = "Ethereum Wallets"
    description_short = (
        "Ethereum blockchain addresses used for tracking decentralized "
        "transactions and digital assets. These wallets can be used to manage "
        "project-specific funds and rewards."
    )
    template_names = {
        "entries": "ethereum/wallets/table.html",
        "entry": "ethereum/wallets/entry.html",
    }

    enabled_component_types = ["dashboard", "entries", "entry"]
