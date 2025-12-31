# -*- coding: utf-8 -*-

from simmate.database.base_data_types import DatabaseTable, table_column

from .priced_items import PricedItem


class PricePoint(DatabaseTable):

    class Meta:
        db_table = "price_catalog__price_points"
        unique_together = (("priced_item", "ticker", "date"),)

    # -------------------------------------------------------------------------

    # This is the the "PriceSource" -- which I keep in the same table for
    # simplicity, even though it results in more disk space in the db.

    priced_item = table_column.ForeignKey(
        PricedItem,
        on_delete=table_column.PROTECT,
        blank=True,
        null=True,
        related_name="price_points",
    )

    ticker_source_options = [
        "Yahoo",  # Yahoo Finance
        "FRED",  # Federal Reserve Bank of St. Louis
        "Wikipedia",  # https://en.wikipedia.org/wiki/Prices_of_chemical_elements
        "Chemical Vendors",  # Sigma Aldrich, Fischer, VWR, etc.
        "Other",
    ]
    ticker_source = table_column.TextField(blank=True, null=True)

    ticker = table_column.TextField(blank=True, null=True)

    # -------------------------------------------------------------------------

    date = table_column.DateTimeField(blank=True, null=True)

    price = table_column.FloatField(blank=True, null=True)

    price_inflation_adj = table_column.FloatField(blank=True, null=True)

    comments = table_column.TextField(blank=True, null=True)

    # -------------------------------------------------------------------------

    # Cached calculations

    # N years *from today's current date*, not the date of this entry

    delta_1y = table_column.FloatField(blank=True, null=True)
    delta_1y_inflation_adj = table_column.FloatField(blank=True, null=True)
    delta_1y_percent = table_column.FloatField(blank=True, null=True)
    delta_1y_percent_inflation_adj = table_column.FloatField(blank=True, null=True)

    delta_5y = table_column.FloatField(blank=True, null=True)
    delta_5y_inflation_adj = table_column.FloatField(blank=True, null=True)
    delta_5y_percent = table_column.FloatField(blank=True, null=True)
    delta_5y_percent_inflation_adj = table_column.FloatField(blank=True, null=True)

    delta_10y = table_column.FloatField(blank=True, null=True)
    delta_10y_inflation_adj = table_column.FloatField(blank=True, null=True)
    delta_10y_percent = table_column.FloatField(blank=True, null=True)
    delta_10y_percent_inflation_adj = table_column.FloatField(blank=True, null=True)

    delta_25y = table_column.FloatField(blank=True, null=True)
    delta_25y_inflation_adj = table_column.FloatField(blank=True, null=True)
    delta_25y_percent = table_column.FloatField(blank=True, null=True)
    delta_25y_percent_inflation_adj = table_column.FloatField(blank=True, null=True)

    # -------------------------------------------------------------------------
