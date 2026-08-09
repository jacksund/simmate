# -*- coding: utf-8 -*-

import numpy

from simmate.toolkit import Molecule

from .base import Featurizer


class MultiFeaturizer(Featurizer):
    """
    Runs multiple featurizers on each molecule and returns their outputs as a
    tuple (one entry per featurizer) per molecule.

    Molecules are converted from SMILES (or any dynamic input) exactly once by
    the inherited _featurize_many_serial logic, then passed to every sub-featurizer —
    avoiding redundant conversions when combining multiple featurizers.

    Subclass and set `featurizers` to use:

        class MyFeaturizer(MultiFeaturizer):
            featurizers = [
                (MorganFingerprint, {"radius": 2, "size": 1024}),
                (MaccsFingerprint, {}),
            ]

    Set `concat = True` to concatenate all feature vectors into a single flat array
    instead of returning a tuple.
    """

    featurizers: list = []  # list of (FeaturizerClass, kwargs_dict)
    concat: bool = False

    @classmethod
    def featurize(cls, molecule: Molecule, **kwargs) -> tuple | numpy.ndarray:
        parts = tuple(
            featurizer_cls.featurize(molecule, **kwargs)
            for featurizer_cls, kwargs in cls.featurizers
        )
        if cls.concat:
            return numpy.concatenate([numpy.ravel(numpy.asarray(p)) for p in parts])
        return parts

    @classmethod
    def get_feature_names(cls, **kwargs) -> list[str] | None:
        all_names = []
        for featurizer_cls, f_kwargs in cls.featurizers:
            names = featurizer_cls.get_feature_names(**f_kwargs)
            if names is None:
                return None
            all_names.extend(names)
        return all_names
