# -*- coding: utf-8 -*-

from simmate.database.base_data_types import DatabaseTable, table_column

from .market_items import MarketItem


class PriceHistory(DatabaseTable):

    class Meta:
        db_table = "price_catalog__price_history"
        unique_together = (("market_item", "date"),)

    market_item = table_column.ForeignKey(
        MarketItem,
        on_delete=table_column.PROTECT,
        blank=True,
        null=True,
        related_name="price_history",
    )

    date = table_column.DateTimeField(blank=True, null=True)

    price = table_column.FloatField(blank=True, null=True)

    price_normalized = table_column.FloatField(blank=True, null=True)
    # for inflation

    comments = table_column.TextField(blank=True, null=True)

    # -------------------------------------------------------------------------

    # 10 years *from the current date*, not the date of this entry

    delta_10y = table_column.FloatField(blank=True, null=True)
    delta_10y_normalized = table_column.FloatField(blank=True, null=True)

    delta_10y_percent = table_column.FloatField(blank=True, null=True)
    delta_10y_percent_normalized = table_column.FloatField(blank=True, null=True)

    # -------------------------------------------------------------------------
