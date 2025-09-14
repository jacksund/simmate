# -*- coding: utf-8 -*-

from datetime import datetime

import numpy
import pandas
from django.utils.timezone import make_aware
from rich.progress import track

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

        from ..clients.fred import FredClient
        from .price_history import PriceHistory

        all_data = FredClient.get_all_data()

        category_lookup = {
            "Chemical Elements": [],
            "Fuels & Energy": ["Electricity"],
            "Crops & Livestock": [],
            "Cryptocurrency": [],
            "Market Index": ["Consumer Price Index"],
            "Other": ["Housing"],
        }

        for name, data in track(all_data.items()):

            category_found = False
            for category, cat_names in category_lookup.items():
                if name in cat_names:
                    category_found = True
                    break

            market_item, _ = cls.objects.update_or_create(
                name=name,
                defaults=dict(
                    category=category if category_found else None,
                    ticker_source="FRED",
                    ticker=FredClient.ticker_map[name],
                ),
            )

            price_objs = [
                PriceHistory(
                    market_item_id=market_item.id,
                    date=make_aware(row.observation_date),
                    price=row.price,  # we use the day's closing price
                )
                for i, row in data.iterrows()
            ]

            PriceHistory.objects.bulk_create(
                price_objs,
                batch_size=1_000,
                ignore_conflicts=True,
            )

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

        for name, data in track(all_data.items()):

            category_found = False
            for category, cat_names in category_lookup.items():
                if name in cat_names:
                    category_found = True
                    break

            market_item, _ = cls.objects.update_or_create(
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
                    date=row.Date,
                    price=row.Close,  # we use the day's closing price
                )
                for i, row in data.iterrows()
            ]

            PriceHistory.objects.bulk_create(
                price_objs,
                batch_size=1_000,
                ignore_conflicts=True,
            )

    @classmethod
    def _load_wikipedia_data(cls):
        pass  # https://en.wikipedia.org/wiki/Prices_of_chemical_elements

    # -------------------------------------------------------------------------

    @classmethod
    def get_buying_power_series(cls):

        cpi = cls.objects.get(name="Consumer Price Index")
        cpi_data = cpi.price_history.order_by("date").to_dataframe(["date", "price"])

        # will be set to $1 and used to normalize others
        todays_buying_power = (
            cpi_data.sort_values("date", ascending=False).iloc[0].price
        )

        # This plot decreases over time because of inflation. It will always have
        # a value of 1 today, but for example, 10 years ago might have a value
        # of 1.25 (i.e., $1 had 25% more buying power 10yrs ago relative to today).
        # When this plot is multiplied by another price plot, you can see an
        # inflation-adjusted plot
        cpi_data["relative_buying_power"] = 1 / (cpi_data.price / todays_buying_power)

        # return only two cols to avoid confusion
        return cpi_data[["date", "relative_buying_power"]]

    @classmethod
    def update_price_history_calcs(cls):

        from .price_history import PriceHistory

        # grab inflation data up front. We use the Consumer Price Index
        # and normalize it to buying power so that we can scale other data
        buying_power_data = cls.get_buying_power_series()

        today = datetime.now()
        # BUG: this might break on leap days
        ten_years_ago = make_aware(
            datetime(
                year=today.year - 10,
                month=today.month,
                day=today.day,
            ),
        )

        for entry in track(cls.objects.filter(name="Bitcoin").all()):

            entry_10y = (
                entry.price_history.filter(date__gte=ten_years_ago)
                .order_by("date")
                .first()
            )
            price_10y = entry_10y.price
            bp_factor_10y = cls.interp_w_datetime(
                original_x=buying_power_data.date,
                original_y=buying_power_data.relative_buying_power,
                new_x=entry_10y.date,
            )
            price_normalized_10y = price_10y * bp_factor_10y

            price_objs = entry.price_history.order_by("date").all()
            for i in price_objs:
                # slow bc I call function one new_x value at time. I can speed
                # up by calling the full series, but code it uglier
                bp_factor = cls.interp_w_datetime(
                    original_x=buying_power_data.date,
                    original_y=buying_power_data.relative_buying_power,
                    new_x=i.date,
                )

                i.price_normalized = i.price * bp_factor
                i.delta_10y = i.price - price_10y
                i.delta_10y_normalized = i.price_normalized - price_normalized_10y
                i.delta_10y_percent = (i.delta_10y / price_10y) * 100
                i.delta_10y_percent_normalized = (
                    i.delta_10y_normalized / price_normalized_10y
                ) * 100

            PriceHistory.objects.bulk_update(
                objs=price_objs,
                fields=[
                    "price_normalized",
                    "delta_10y",
                    "delta_10y_normalized",
                    "delta_10y_percent",
                    "delta_10y_percent_normalized",
                ],
            )

    @staticmethod
    def interp_w_datetime(original_x, original_y, new_x):
        # DEPREC: from scipy.interpolate import interp1d
        # For other options look at...
        # https://docs.scipy.org/doc/scipy/tutorial/interpolate/1D.html
        original_x = original_x.astype("int64") // 1e9  # to seconds
        new_x = pandas.Series(new_x).astype("int64") // 1e9  # to seconds
        new_y = numpy.interp(new_x, original_x, original_y)[0]
        return new_y

    # -------------------------------------------------------------------------
