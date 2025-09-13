# -*- coding: utf-8 -*-

try:
    import yfinance
except:
    raise Exception(
        "Missing app-specific dependencies. Make sure to read our installation guide."
        "The `price_catalog` app requires an additional dependency: `yfinance`."
        "Install this with `pip install yfinance` (conda install is broken)"
        # conda install -c conda-forge yfinance
    )


class YahooFinanceClient:
    """
    A minimal wrapper around the `yfinance` package api
    """

    ticker_map = {
        # Metals
        "Gold": "GC=F",
        "Silver": "SI=F",
        # "Platinum": "PL=F",
        # "Palladium": "PA=F",
        # "Copper": "HG=F",
        # # Fuels
        # "Crude Oil": "CL=F",
        # "Natural Gas": "NG=F",
        # # Crops
        # "Lumber": "LBR=F",
        # "Soybeans": "ZS=F",
        # "Corn": "ZC=F",
        # "Wheat": "KE=F",
        # "Coffee": "KC=F",
        # "Sugar": "SB=F",
        # "Cocoa": "CC=F",
        # "Cotton": "CT=F",
        # # Livestock
        # "Hogs": "HET=F",
        # "Cattle": "LE=F",
        # # Crypto
        # "Bitcoin": "BTC-USD",
        # "Ethereum": "ETH-USD",
        # "Solana": "SOL-USD",
        # # Indexes
        # "S&P GSCI": "GD=F",  # Commodity Index
        # "S&P 500": "SPY",
        # "Total Market Index": "FSKAX",
    }

    @classmethod
    def get_all_data(cls):
        """
        Uses the list of tickers in `ticker_map` to grab all datasets
        """
        final_data = {}
        for name in cls.ticker_map.items():
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
    def get_ticker_data(ticker: str, peroid: str = "max"):
        """
        Uses the Yahoo ticker value to grab data. Can be any ticker in the live site
        such as `SPY` or `GOOGL`
        """
        data = yfinance.Ticker(ticker).history(period=peroid)
        data.reset_index(inplace=True)  # bc we want Date as a col, not the index
        return data
