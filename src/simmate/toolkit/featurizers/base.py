# -*- coding: utf-8 -*-

from concurrent.futures import ProcessPoolExecutor

import numpy
import pandas
from rich.progress import track

from simmate.toolkit import Molecule
from simmate.utilities import chunk_list


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
    def featurize_many(
        cls,
        molecules: list[Molecule] | list[any],  # any bc we use from_dynamic
        parallel: bool = False,
        dataframe_format: str = "list",  # numpy, polars, pandas, or list
        **kwargs,
    ) -> list:
        """
        Generates fingerprints for a list of molecules in a serial or parallel manner.
        """
        if not parallel:
            features = cls._featurize_many_serial(molecules, **kwargs)
        else:
            features = cls._featurize_many_parallel(molecules, **kwargs)

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

    @classmethod
    def _featurize_many_serial(
        cls,
        molecules: list[Molecule],
        progress_bar: bool = True,
        **kwargs,
    ):
        """
        Generates fingerprints for a list of molecules in serial
        (so one at a time on a single core).
        """
        features_list = []
        for molecule in track(molecules, disable=not progress_bar):
            if not isinstance(molecule, Molecule):
                molecule = Molecule.from_dynamic(molecule)
            features = cls.featurize(molecule, **kwargs)
            features_list.append(features)
        return features_list

    @classmethod
    def _featurize_many_parallel(
        cls,
        molecules: list[Molecule],
        chunk_size: int = 1_000,
        max_workers: int = None,
        **kwargs,
    ):
        """
        Generates fingerprints for a list of molecules in parallel.
        """

        # note, we submit to the proccess pool in batches rather than normal
        # like this:
        #   with ProcessPoolExecutor() as executor:
        #       futures = [executor.submit(cls.featurize, molecule, **kwargs) for molecule in molecules]
        #       return [f.result() for f in track(futures)]
        # We do this to prevent the io from being the bottleneck.
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(
                    cls._featurize_many_serial, chunk, progress_bar=False, **kwargs
                )
                for chunk in chunk_list(full_list=molecules, chunk_size=chunk_size)
            ]
            # flatten results before returning
            return [item for future in track(futures) for item in future.result()]
