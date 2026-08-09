# -*- coding: utf-8 -*-

from pathlib import Path

import pandas


def load_bcpc_news_archive() -> pandas.DataFrame:
    """
    Loads a CSV from running the `get_all_news_data.BcpcWebScrapper` fxn
    previously. This helps save on LLM calls and includes a bit of
    manual cleanup, but is likely out of date compared to the live site.

    This dataset was pulled from:
        http://www.bcpcpesticidecompendium.org/news/index.html
    """
    # Set the full path to the file (which is the same dir as this script)
    datafile = Path(__file__).parent / "news_archive.csv"
    # give back as df
    data = pandas.read_csv(datafile)
    return data


BCPC_NEWS_ARCHIVE = load_bcpc_news_archive()
