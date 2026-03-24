# -*- coding: utf-8 -*-

import pandas
from simmate.website.htmx.components import DynamicTableForm

from .models import PricedItem, PricePoint


class PricedItemTable(DynamicTableForm):
    table = PricedItem
    html_display_name = "Market Data & Price Catalog"
    html_description_short = (
        "A catalog of prices and economic indicators spanning chemicals, "
        "stocks, commodities, and more. This data helps in tracking the "
        "costs of laboratory reagents and broader macroeconomic trends."
    )
    template_names = {
        "default": "data_explorer/table_about.html",
        "entries": "price_catalog/priced_items/table.html",
        "entry": "price_catalog/priced_items/entry.html",
    }

    enable_html_report = True
    report_df_columns = ["id"]

    def get_report_from_df(self, df: pandas.DataFrame):
        return {"test": 123}


class PricePointTable(DynamicTableForm):
    table = PricePoint
