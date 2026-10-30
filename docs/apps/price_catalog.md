# Price Catalog

--------------------------------------------------------------------------------

## About

The `price_catalog` app tracks long-term price trends for chemical elements, chemical indexes, fuels, crops, cryptocurrencies, and market indexes. Prices are pulled from [FRED](https://fred.stlouisfed.org/), [Yahoo Finance](https://finance.yahoo.com/), and Wikipedia, and are only updated at the start of each month (this app is for long-term trends, not live trading).

--------------------------------------------------------------------------------

## Installation

1. This app is installed by default. If you removed it, add it back with:
``` bash
simmate config add price_catalog
```

2. Update your database to include custom tables from the app:
``` shell
simmate database update
```

3. (optional) To pull new prices from Yahoo Finance, install the app's extra dependencies:
``` bash
uv pip install "simmate[price_catalog]"
```

--------------------------------------------------------------------------------
