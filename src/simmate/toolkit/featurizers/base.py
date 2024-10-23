# -*- coding: utf-8 -*-

from rich.progress import track

from simmate.toolkit import Molecule


class Featurizer:
    """
    Abstract base class for generating fingerprints for a list of molecules.
    """

    # This class is largely inspired by Matminer's featurizer class and can be
    # considered a fork/refactor of it:
    #     https://github.com/hackingmaterials/matminer/blob/main/matminer/featurizers/base.py

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
        molecules: list[Molecule],
        parallel: bool = False,
        **kwargs,
    ) -> list:
        """
        Generates fingerprints for a list of molecules in a serial or parallel manner.
        """
        if not parallel:
            return cls._featurize_many_serial(molecules, **kwargs)
        else:
            return cls._featurize_many_parallel(molecules, **kwargs)

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
            features = cls.featurize(molecule, **kwargs)
            features_list.append(features)
        return features_list

    @classmethod
    def _featurize_many_parallel(
        cls,
        molecules: list[Molecule],
        batch_size: int = 10000,
        use_serial_batches: bool = False,
        batch_size_serial: int = 500,
        **kwargs,
    ):
        """
        Generates fingerprints for a list of molecules in parallel.
        """
        # Use this method to help. Maybe write a utility function for batch
        # submitting and serial-batch submitting to dask too.
        # https://github.com/jacksund/simmate/blob/17d926fe5ee8f183240a4526982b4d7fd5d7042b/src/simmate/toolkit/creators/structure/base.py#L67
        raise NotImplementedError(
            "This method is still being written. Try parallel=False."
        )
