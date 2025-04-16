# -*- coding: utf-8 -*-

from pathlib import Path

import pandas

from simmate.toolkit import Molecule


class SmartsSet:
    """
    Contains common functionality for a list of SMARTS strings and how you
    might use them.
    """

    source_file: str = None
    """
    File that contains all the SMARTS queries and their names (+ any other metadata).
    
    There MUST be columns for "smarts_str" and "name", as these columns
    are assumed and used in other methods.
    """

    # -------------------------------------------------------------------------

    @classmethod
    def get_counts(
        cls,
        molecule: Molecule,
        include_misses: bool = False,
    ) -> dict:
        counts = {}
        for name, smarts in cls.smarts_dict.items():
            num_match = molecule.num_smarts_match(smarts)
            if num_match or (include_misses and not num_match):
                counts.update({name: num_match})
        return counts

    @classmethod
    def get_matches(cls, molecule: Molecule) -> dict:
        matches = []
        for name, smarts in cls.smarts_dict.items():
            is_match = molecule.is_smarts_match(smarts)
            if is_match:
                matches.append(name)
        return matches

    @classmethod
    def get_total_count(cls, molecule: Molecule):
        ind_counts = cls.get_counts(molecule)
        total = sum(ind_counts.values())
        return total

    @classmethod
    def get_weighted_count(
        cls,
        molecule: Molecule,
        weight_col: str = "weight",
    ):
        ind_counts = cls.get_counts(molecule)
        weights = cls.smarts_data.set_index("name")[weight_col].to_dict()
        total = sum([weights[name] * count for name, count in ind_counts.items()])
        return total

    # -------------------------------------------------------------------------

    @classmethod
    @property
    def smarts_data(cls) -> pandas.DataFrame:
        # check for cached version first
        if cls._smarts_data is not None:
            return cls._smarts_data
        # if no cache, load the set

        # Grab the directory of this current python file
        current_directory = Path(__file__).parent

        # Set the full path to the data csv file
        datafile = Path(cls.source_file)
        if not datafile.exists():
            datafile = current_directory / cls.source_file

        # Load the csv file into a pandas dataframe
        data = pandas.read_csv(datafile)

        if "smarts_str" not in data.columns or "name" not in data.columns:
            raise Exception(
                "SmartsSet classes require an input file with column names "
                "'smarts_str' and 'name' available."
            )

        # convert all smarts to mol objects
        data["smarts_mol"] = [
            Molecule.from_smarts(s, clean_benchtop_conventions=False)
            for s in data.smarts_str
        ]

        # set cache for faster loading next time
        cls._smarts_data = data

        return data

    _smarts_data: pandas.DataFrame = None
    """
    This is a cached set of the `smarts_data` property. Users should just
    interact with `smarts_data` and ingnore this internal
    """
    # OPTIMIZE: cached_property + classmethod don't work well together

    # -------------------------------------------------------------------------

    @classmethod
    @property
    def smarts_dict(cls) -> pandas.DataFrame:
        # check for cached version first
        if cls._smarts_dict is not None:
            return cls._smarts_dict
        # if no cache, load the set

        # convert the dataframe to a dictionary of {name: mol_obj}
        data = cls.smarts_data
        smarts_dict = dict(zip(data.name, data.smarts_mol))

        # set cache for faster loading next time
        cls._smarts_dict = smarts_dict

        return smarts_dict

    _smarts_dict: dict = None
    """
    This is a cached set of the `smarts_dict` property. Users should just
    interact with `smarts_dict` and ingnore this internal
    """

    # -------------------------------------------------------------------------
