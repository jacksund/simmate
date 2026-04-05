# -*- coding: utf-8 -*-

from simmate.website.data_explorer.components import DynamicTableForm

from ..models import PricedItem


class PricedItemTable(DynamicTableForm):
    table = PricedItem
    display_name = "Market Data & Price Catalog"
    description_short = (
        "A catalog of prices and economic indicators spanning chemicals, "
        "stocks, commodities, and more. This data helps in tracking the "
        "costs of laboratory reagents and broader macroeconomic trends."
    )
    template_names = {
        "default": "data_explorer/table_about.html",
        "entries": "price_catalog/priced_items/table.html",
        "entry": "price_catalog/priced_items/entry.html",
    }

    enable_report = True
    report_df_columns = ["id"]
