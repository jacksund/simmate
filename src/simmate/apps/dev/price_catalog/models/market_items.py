# -*- coding: utf-8 -*-

from django.utils.timezone import make_aware

from simmate.database.base_data_types import DatabaseTable, table_column


class MarketItem(DatabaseTable):

    class Meta:
        db_table = "price_catalog__market_items"

    category_options = [
        "Chemical Elements",
        "Fuels & Energy",
        "Crops & Livestock",
        "Cryptocurrency",
        "Market Index",
        "Other",  # e.g. housing
    ]
    category = table_column.TextField(blank=True, null=True)

    name = table_column.TextField(blank=True, null=True)

    ticker = table_column.TextField(blank=True, null=True)

    ticker_source_options = [
        "Yahoo",  # Yahoo Finance
        "FRED",  # Federal Reserve Bank of St. Louis
        "Wikipedia",  # https://en.wikipedia.org/wiki/Prices_of_chemical_elements
        "Vendor(s)",  # Sigma Aldrich, Fischer, eMolecules, ACD, etc.
        "Other",
    ]
    ticker_source = table_column.TextField(blank=True, null=True)

    comments = table_column.TextField(blank=True, null=True)

    # -------------------------------------------------------------------------

    global_abundance = table_column.FloatField(blank=True, null=True)
    # count
    # kg
    # infinite (for indexes/housing)

    price = table_column.FloatField(blank=True, null=True)

    price_10y_stats = table_column.JSONField(blank=True, null=True)
    # Start
    # Current
    # Min
    # Max
    # % change
    # % change normalized for inflation

    # -------------------------------------------------------------------------

    # Normalized values

    global_abundance_kg = table_column.FloatField(blank=True, null=True)

    global_abundance_mg_per_kg_crust = table_column.FloatField(blank=True, null=True)

    price_per_kg = table_column.FloatField(blank=True, null=True)

    # -------------------------------------------------------------------------

    @classmethod
    def _load_fred_data(cls):
        pass

    @classmethod
    def _load_yfinance_data(cls):
        from ..clients.yfinance import YahooFinanceClient
        from .price_history import PriceHistory

        all_data = YahooFinanceClient.get_all_data()

        category_lookup = {
            "Chemical Elements": [
                "Gold",
                "Silver",
                "Platinum",
                "Palladium",
                "Copper",
            ],
            "Fuels & Energy": [
                "Crude Oil",
                "Natural Gas",
            ],
            "Crops & Livestock": [
                "Lumber",
                "Soybeans",
                "Corn",
                "Wheat",
                "Coffee",
                "Sugar",
                "Cocoa",
                "Cotton",
                "Hogs",
                "Cattle",
            ],
            "Cryptocurrency": [
                "Bitcoin",
                "Ethereum",
                "Solana",
            ],
            "Market Index": [
                "S&P GSCI",
                "S&P 500",
                "Total Market Index",
            ],
            "Other": [],
        }

        for name, data in all_data.items():
            breakpoint()
            category_found = False
            for category, cat_names in category_lookup.items():
                if name in cat_names:
                    category_found = True
                    break

            _, market_item = cls.objects.update_or_create(
                name=name,
                defaults=dict(
                    category=category if category_found else None,
                    ticker_source="Yahoo",
                    ticker=YahooFinanceClient.ticker_map[name],
                ),
            )

            price_objs = [
                PriceHistory(
                    market_item_id=market_item.id,
                    date=make_aware(row.Date),
                    price=row.Close,  # we use the day's closing price
                )
                for i, row in data.iterrows()
            ]

            cls.objects.bulk_create(
                price_objs,
                batch_size=1_000,
                ignore_conflicts=True,
            )

    @classmethod
    def _load_wikipedia_data(cls):
        pass  # https://en.wikipedia.org/wiki/Prices_of_chemical_elements
