# -*- coding: utf-8 -*-

from pathlib import Path

import pandas


def load_greek_gods_data() -> pandas.DataFrame:
    """
    Loads a basic dataset of Greek Gods (~450 total).

    This dataset was pulled from:
        https://github.com/katkaypettitt/greek-gods/tree/main
    """
    # Set the full path to the file (which is the same dir as this script)
    datafile = Path(__file__).parent / "greek_gods.csv"
    # give back as df
    data = pandas.read_csv(datafile)
    return data


GREEK_GODS = load_greek_gods_data()
