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
        # Producer Price Index (PPI):
        #   sections for "Industrial Chemicals" or "Chemicals and Allied Products"
        # Make sure you look at this link to see the full tree of these tickers
        # and how they relate to one another (some are subcategories of others)
        # https://fred.stlouisfed.org/release/tables?rid=46&eid=142872#snid=142874
        "Chemicals & Allied Products": "WPU06",
        "Industrial Chemicals": "WPU061",
        #
        "Inorganic Chemicals": "WPU0613",
        "Organic Chemicals": "WPU0614",
        "Industrial Gases": "WPU067903",
        #
        "Carbon": "WPU06790918",  # Carbon Black
        "Carbon Dioxide": "WPU06790302",
        "Nitrogen": "WPU06790303",
        "Oxygen": "WPU06790304",
        "Aluminum Compounds": "WPU06130209",
        "Sulfuric Acid": "WPU0613020T1",
        "NaCl": "WPU06130271",  # Rock Salt
        "Ethanol": "WPU06140341",
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
        Uses the FRED ticker value to grab data. Can be any ticker in the live site
        such as `SPY` or `GOOGL`
        """
        url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={ticker}"
        data = pandas.read_csv(url, parse_dates=["observation_date"])
        data.rename(columns={ticker: "price"}, inplace=True)
        return data
