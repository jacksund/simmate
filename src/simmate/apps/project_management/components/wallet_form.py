# -*- coding: utf-8 -*-

from simmate.website.data_explorer.components import DynamicTableForm

from ..models import Wallet


class WalletForm(DynamicTableForm):
    table = Wallet

    template_names = {
        "default": "data_explorer/table_about.html",
        "entries": "project_management/wallet/table.html",
        "entry": "project_management/wallet/view.html",
    }

    display_name = "Wallets"
    description_short = (
        "Digital accounts that contain USDC or Token assets for budgeting "
        "and spending. Wallets help track and limit the resources "
        "allocated to specific projects or users."
    )
