# -*- coding: utf-8 -*-

import logging
from datetime import datetime

import numpy
import pandas
import plotly.express as plotly_express
import plotly.graph_objects as plotly_go
from django.utils.timezone import make_aware
from rich.progress import track

from simmate.database.base_data_types import DatabaseTable, table_column


class PricedItem(DatabaseTable):

    class Meta:
        db_table = "price_catalog__priced_items"

    html_display_name = "Market Data & Price Catalog"
    html_description_short = (
        "Prices and economic indicators spanning common chemicals, stocks, "
        "commodities, cryptocurrencies, and macroeconomic metrics."
    )

    html_entries_template = "price_catalog/priced_items/table.html"
    html_entry_template = "price_catalog/priced_items/entry.html"

    # html_form_component = "priced-item-form"
    # html_enabled_forms = ["search"]

    # -------------------------------------------------------------------------

    category_options = [
        "Chemical Index",
        "Chemical Elements",
        # "Chemical Solvents",
        # "Chemical Reagents",
        "Fuels & Energy",
        "Crops & Livestock",
        "Cryptocurrency",
        "Market Index",
        "Other",  # e.g. housing
    ]
    category = table_column.TextField(blank=True, null=True)

    name = table_column.TextField(blank=True, null=True)

    preferred_source_options = [
        "Yahoo",  # Yahoo Finance
        "FRED",  # Federal Reserve Bank of St. Louis
        "Wikipedia",  # https://en.wikipedia.org/wiki/Prices_of_chemical_elements
        "Chemical Vendors",  # Sigma Aldrich, Fischer, VWR, etc.
        "Other",
    ]
    preferred_source = table_column.TextField(blank=True, null=True)

    comments = table_column.TextField(blank=True, null=True)

    # -------------------------------------------------------------------------

    price = table_column.FloatField(blank=True, null=True)
    # filled using the most recent price point of the preferred source

    # per kg
    # per share
    # per kW/hr
    price_unit = table_column.TextField(blank=True, null=True)

    global_abundance = table_column.FloatField(blank=True, null=True)

    # count
    # kg
    # infinite (for indexes/housing)
    global_abundance_unit = table_column.TextField(blank=True, null=True)

    market_cap = table_column.FloatField(blank=True, null=True)
    # price * global_abundance

    # -------------------------------------------------------------------------

    # Standardized values

    global_abundance_kg = table_column.FloatField(blank=True, null=True)

    global_abundance_mg_per_kg_crust = table_column.FloatField(blank=True, null=True)

    price_per_kg = table_column.FloatField(blank=True, null=True)

    # -------------------------------------------------------------------------

    # Price history stats

    # start ($)
    # min ($)
    # max ($)
    # change (%)
    # change_inflation_adj (%) for inflation

    years_ago_options = [1, 5, 10, 25]

    price_1y_stats = table_column.JSONField(blank=True, null=True)

    price_5y_stats = table_column.JSONField(blank=True, null=True)

    price_10y_stats = table_column.JSONField(blank=True, null=True)

    price_25y_stats = table_column.JSONField(blank=True, null=True)

    # -------------------------------------------------------------------------

    @classmethod
    def get_figure(cls):

        from .price_points import PricePoint

        data = PricePoint.objects.order_by("priced_item__name", "date").to_dataframe(
            [
                "priced_item__name",
                "date",
                # "price",
                # "price_inflation_adj",
                # "delta_10y",
                # "delta_10y_inflation_adj",
                # "delta_10y_percent",
                "delta_10y_percent_inflation_adj",
            ]
        )
        fig = plotly_express.line(
            data,
            x="date",
            y="delta_10y_percent_inflation_adj",
            color="priced_item__name",
        )
        fig.show(renderer="browser")

    def get_price_figure(self, inflation_adj: bool = False):

        y_col = "price" if not inflation_adj else "price_inflation_adj"
        columns = ["date", y_col]
        data = self.price_points.order_by("date").to_dataframe(columns)

        fig = plotly_express.area(
            data,
            x="date",
            y=y_col,
        )

        fig.update_layout(yaxis_tickprefix="$")

        fig.show(renderer="browser")

    def get_delta_10y_figure(self, inflation_adj: bool = False):

        ten_years_ago = self.get_10y_datetime()
        y_col = (
            "delta_10y_percent"
            if not inflation_adj
            else "delta_10y_percent_inflation_adj"
        )
        columns = ["date", y_col]
        data = self.price_points.filter(date__gte=ten_years_ago).to_dataframe(columns)

        # Separate positive and negative parts
        rel_change = data[y_col]
        pos = numpy.where(rel_change > 0, rel_change, 0) / 100
        neg = numpy.where(rel_change < 0, rel_change, 0) / 100

        fig = plotly_go.Figure()

        fig.add_trace(
            plotly_go.Scatter(
                x=data.date,
                y=pos,
                fill="tozeroy",
                name="Positive",
                line=dict(color="green"),
                showlegend=False,
            )
        )

        fig.add_trace(
            plotly_go.Scatter(
                x=data.date,
                y=neg,
                fill="tozeroy",
                name="Negative",
                line=dict(color="red"),
                showlegend=False,
            )
        )

        # Black line at Zero
        fig.add_trace(
            plotly_go.Scatter(
                x=data.date,
                y=[0] * len(data),
                mode="lines",
                line=dict(color="black", width=3),
                name="Zero",
                showlegend=False,
            )
        )

        fig.update_layout(yaxis_tickformat=".0%")

        fig.show(renderer="browser")

    # -------------------------------------------------------------------------

    @classmethod
    def get_buying_power_series(cls, reference: str = "Consumer Price Index"):

        cpi = cls.objects.get(name=reference)
        cpi_data = cpi.price_points.order_by("date").to_dataframe(["date", "price"])

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
    def update_price_points_calcs(cls):

        from .price_points import PricePoint

        # grab inflation data up front. We use the Consumer Price Index
        # and normalize it to buying power so that we can scale other data
        buying_power_data = cls.get_buying_power_series()

        for entry in track(cls.objects.all()):

            for years_ago in cls.years_ago_options:

                year_ago_dt = cls.get_years_ago_datetime(years_ago)

                entry_closest = (
                    entry.price_points.filter(date__gte=year_ago_dt)
                    .order_by("date")
                    .first()
                )

                # check that the date is within at least 6months
                if (
                    entry_closest.date - year_ago_dt
                ).total_seconds() >= 60 * 60 * 24 * 30 * 6:
                    continue

                price_closest = entry_closest.price
                bp_factor_closest = cls.interp_w_datetime(
                    original_x=buying_power_data.date,
                    original_y=buying_power_data.relative_buying_power,
                    new_x=entry_closest.date,
                )
                price_inflation_adj_closest = price_closest * bp_factor_closest

                price_objs = entry.price_points.order_by("date").all()
                for i in price_objs:

                    # This is the bottleneck + slow bc I call function one
                    # new_x value at time. I can speed up by calling the full
                    # series, but code would be uglier. I cache this data and
                    # run once per day, so I'm okay with the slowdown
                    bp_factor = cls.interp_w_datetime(
                        original_x=buying_power_data.date,
                        original_y=buying_power_data.relative_buying_power,
                        new_x=i.date,
                    )

                    price_inflation_adj = i.price * bp_factor

                    delta = i.price - price_closest

                    delta_inflation_adj = (
                        price_inflation_adj - price_inflation_adj_closest
                    )

                    delta_percent = (delta / price_closest) * 100

                    delta_percent_inflation_adj = (
                        delta_inflation_adj / price_inflation_adj_closest
                    ) * 100

                    update_map = {
                        "price_inflation_adj": price_inflation_adj,
                        f"delta_{years_ago}y": delta,
                        f"delta_{years_ago}y_inflation_adj": delta_inflation_adj,
                        f"delta_{years_ago}y_percent": delta_percent,
                        f"delta_{years_ago}y_percent_inflation_adj": delta_percent_inflation_adj,
                    }
                    for k, v in update_map.items():
                        setattr(i, k, v)

                PricePoint.objects.bulk_update(
                    objs=price_objs,
                    fields=[
                        "price_inflation_adj",
                        f"delta_{years_ago}y",
                        f"delta_{years_ago}y_inflation_adj",
                        f"delta_{years_ago}y_percent",
                        f"delta_{years_ago}y_percent_inflation_adj",
                    ],
                )

                # update parent object
                entry.price = entry.price_points.order_by("-date").first().price
                all_prices = [p.price for p in price_objs]
                stats = {
                    "start": price_closest,
                    "min": min(all_prices),
                    "max": max(all_prices),
                    "change": ((entry.price - price_closest) / price_closest) * 100,
                    "change_inflation_adj": (
                        (entry.price - price_inflation_adj_closest) / price_closest
                    )
                    * 100,
                }
                setattr(entry, f"price_{years_ago}y_stats", stats)
                entry.save()

    @staticmethod
    def interp_w_datetime(original_x, original_y, new_x):
        # DEPREC: from scipy.interpolate import interp1d
        # For other options look at...
        # https://docs.scipy.org/doc/scipy/tutorial/interpolate/1D.html
        original_x = original_x.astype("int64") // 1e9  # to seconds
        new_x = pandas.Series(new_x).astype("int64") // 1e9  # to seconds
        new_y = numpy.interp(new_x, original_x, original_y)[0]
        return new_y

    @staticmethod
    def get_years_ago_datetime(years: int):
        today = datetime.now()
        ten_years_ago = make_aware(
            datetime(
                year=today.year - years,
                month=today.month,
                day=today.day,  # BUG: this might break on leap days
            ),
        )
        return ten_years_ago

    # -------------------------------------------------------------------------

    @classmethod
    def _load_data(cls):
        # cls._load_wikipedia_data()
        cls._load_yfinance_data()
        cls._load_fred_data()
        # cls.update_price_points_calcs()

    @classmethod
    def _load_fred_data(cls):

        from ..clients.fred import FredClient
        from .price_points import PricePoint

        all_data = FredClient.get_all_data()

        category_lookup = {
            "Chemical Index": [
                "Chemicals",
                "Industrial Chemicals",
                "Inorganic Chemicals",
                "Organic Chemicals",
                "Industrial Gases",
            ],
            "Chemical Elements": [
                "Carbon",
                "Nitrogen",
                "Oxygen",
                "Aluminum",
            ],
            "Fuels & Energy": ["Electricity"],
            "Crops & Livestock": [],
            "Cryptocurrency": [],
            "Market Index": ["Consumer Price Index"],
            "Other": ["Housing"],
        }

        for name, data in track(all_data.items()):

            # sometimes a row is missing the price and/or timestamp
            data.dropna(inplace=True)

            category_found = False
            for category, cat_names in category_lookup.items():
                if name in cat_names:
                    category_found = True
                    break

            priced_item, _ = cls.objects.update_or_create(
                name=name,
                defaults=dict(
                    category=category if category_found else None,
                ),
            )

            price_objs = [
                PricePoint(
                    priced_item_id=priced_item.id,
                    ticker_source="FRED",
                    ticker=FredClient.ticker_map[name],
                    #
                    date=make_aware(row.observation_date),
                    price=row.price,  # we use the day's closing price
                )
                for i, row in data.iterrows()
            ]

            # TODO: ensure I don't create duplicate entries on update
            PricePoint.objects.bulk_create(
                price_objs,
                batch_size=1_000,
                ignore_conflicts=True,
            )

    @classmethod
    def _load_yfinance_data(cls):
        from ..clients.yfinance import YahooFinanceClient
        from .price_points import PricePoint

        all_data = YahooFinanceClient.get_all_data()

        category_lookup = {
            "Chemical Index": [],
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

            priced_item, _ = cls.objects.update_or_create(
                name=name,
                defaults=dict(
                    category=category if category_found else None,
                ),
            )

            price_objs = [
                PricePoint(
                    priced_item_id=priced_item.id,
                    ticker_source="Yahoo",
                    ticker=YahooFinanceClient.ticker_map[name],
                    #
                    date=row.Date,
                    price=row.Close,  # we use the day's closing price
                )
                for i, row in data.iterrows()
            ]

            PricePoint.objects.bulk_create(
                price_objs,
                batch_size=1_000,
                ignore_conflicts=True,
            )

    @classmethod
    def _load_wikipedia_data(cls):

        raise NotImplementedError()

        from ..data import WIKIPEDIA_PRICES_OF_ELEMENTS_DATA

        for row in WIKIPEDIA_PRICES_OF_ELEMENTS_DATA.itertuples():
            priced_item, _ = cls.objects.update_or_create(
                name=row.name,
                defaults=dict(
                    category="Chemical Elements",
                    ticker_source="Wikipedia",
                    ticker=row.symbol,
                    price=row.price_per_kg,
                    price_unit="per kg",
                    price_per_kg=row.price_per_kg,
                    global_abundance=row.total_mass_kg,
                    global_abundance_unit="kg",
                    market_cap=row.price_per_kg * row.total_mass_kg,
                    global_abundance_kg=row.total_mass_kg,
                    global_abundance_mg_per_kg_crust=row.abundance_mg_kg,
                    # TODO: store metadata of year + source + price_per_l + tec
                ),
            )
