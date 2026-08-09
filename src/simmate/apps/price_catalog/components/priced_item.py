# -*- coding: utf-8 -*-

from simmate.website.data_explorer.components import TableComponent

from ..models import PricedItem


class PricedItemComponent(TableComponent):
    table = PricedItem
    display_name = "Market Data & Price Catalog"
    description_short = (
        "A catalog of prices and economic indicators spanning chemicals, "
        "stocks, commodities, and more. This data helps in tracking the "
        "costs of laboratory reagents and broader macroeconomic trends."
    )
    template_names = {
        "entries": "price_catalog/priced_items/table.html",
        "entry": "price_catalog/priced_items/entry.html",
    }

    enabled_component_types = ["dashboard", "entries", "entry"]

    enable_report = True
    report_df_columns = ["id"]
