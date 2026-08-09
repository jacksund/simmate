# -*- coding: utf-8 -*-

import numpy
import pandas
from rich.progress import track

from simmate.toolkit import Molecule
from simmate.utils import dispatch


class Featurizer:
    """
    Abstract base class for generating fingerprints for a list of molecules.
    """

    # This class is largely inspired by Matminer's featurizer class and can be
    # considered a fork/refactor of it:
    #     https://github.com/hackingmaterials/matminer/blob/main/matminer/featurizers/base.py

    @classmethod
    def get_feature_names(cls, **kwargs) -> list[str]:
        """
        Grabs a list of the feature names to optionally be used when converting
        the list of features to a dataframe.
        """
        return None

    @staticmethod
    def featurize(molecule: Molecule):
        """
        Generates a fingerprint for a single molecule.
        """
        raise NotImplementedError(
            "Make sure you write a custom generate_fingerprint method!"
        )

    @classmethod
    def _featurize_dynamic(cls, molecule, **kwargs):
        if not isinstance(molecule, Molecule):
            molecule = Molecule.from_dynamic(molecule)
        return cls.featurize(molecule, **kwargs)

    @classmethod
    def featurize_many(
        cls,
        molecules: list[Molecule] | list[any],  # any bc we use from_dynamic
        parallel: bool | str = False,
        dataframe_format: str = "list",  # numpy, polars, pandas, or list
        **kwargs,
    ) -> list:
        """
        Generates fingerprints for a list of molecules in a serial or parallel manner.
        """
        features = dispatch(
            molecules,
            cls._featurize_dynamic,
            parallel=parallel,
            **kwargs,
        )

        if dataframe_format == "list":
            return features
        elif dataframe_format == "numpy":
            return numpy.array(features)
        elif dataframe_format == "pandas":
            return pandas.from_numpy(
                data=numpy.array(features), schema=cls.get_feature_names(**kwargs)
            )
        elif dataframe_format == "polars":
            import polars  # not an official dep yet

            return polars.from_numpy(
                data=numpy.array(features), schema=cls.get_feature_names(**kwargs)
            )
        else:
            raise Exception(f"Unknown `dataframe_format`: {dataframe_format}")
