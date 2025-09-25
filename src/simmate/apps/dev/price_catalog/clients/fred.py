# -*- coding: utf-8 -*-

import pandas
from rich.progress import track

# NOTE: the is a FRED REST API and even a fredapi python package. But there
# are URLs for downloadling CSV files without an API key... So I just use those.
# We are doing this very infrequently so we shouldn't run into rate limits


class FredClient:
    """
    A minimal client to download CSV data from the Federal Reserve Bank of
    St. Louis (FRED)
    """

    ticker_map = {
        "Electricity": "CUSR0000SEHF01",  # or APU000072610
        "Housing": "CSUSHPINSA",
        "Consumer Price Index": "CPIAUCSL",  # use for inflation metrics
    }

    @classmethod
    def get_all_data(cls):
        """
        Uses the list of tickers in `ticker_map` to grab all datasets
        """
        final_data = {}
        for name in track(cls.ticker_map):
            final_data[name] = cls.get_data(name)
        return final_data

    @classmethod
    def get_data(cls, name: str):
        """
        Grabs data using the common name. See the `ticker_map` for values
        """
        ticker_str = cls.ticker_map[name]
        return cls.get_ticker_data(ticker_str)

    @staticmethod
    def get_ticker_data(ticker: str):
        """
        Uses the Yahoo ticker value to grab data. Can be any ticker in the live site
        such as `SPY` or `GOOGL`
        """
        url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={ticker}"
        data = pandas.read_csv(url, parse_dates=["observation_date"])
        data.rename(columns={ticker: "price"}, inplace=True)
        return data
