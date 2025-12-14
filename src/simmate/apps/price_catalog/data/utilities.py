# -*- coding: utf-8 -*-

from pathlib import Path

import pandas


def load_wikipedia_data() -> pandas.DataFrame:
    """
    Loads a snapshot dataset from the "Prices of chemical elements" page

    This dataset was pulled from:
        https://en.wikipedia.org/wiki/Prices_of_chemical_elements

    Note, I used Gemini to web scrape bc I'm lazy. The following prompt was used
    to generate the CSV file, and I spot checked only a little to confirm:

        '''
        Grab the table from this link and convert it to a CSV:
        https://en.wikipedia.org/wiki/Prices_of_chemical_elements

        The following should be done too:
        - split the "abundance" column into two columns, one for mg/kg and one for total mass
        - use "e" notation instead of "x10^" so that values are floats
        - standardize numerical columns (e.g. convert ranges to single value and exclude any >, <, ~, etc symbols)
        - leave a cell empty instead of using text like "Not traded"
        - use the columns names of...
            z, symbol, name, density_kg_l, abundance_mg_kg, total_mass_kg,
            price_per_kg, price_per_l, year, source, notes
        '''

    """
    datafile = Path(__file__).parent / "wikipedia_prices_of_elements.csv"
    data = pandas.read_csv(datafile)
    return data


WIKIPEDIA_PRICES_OF_ELEMENTS_DATA = load_wikipedia_data()
