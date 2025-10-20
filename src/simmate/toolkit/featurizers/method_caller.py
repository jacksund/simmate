# -*- coding: utf-8 -*-

import numpy

from simmate.toolkit import Molecule
from simmate.toolkit.featurizers.base import Featurizer


class MethodCaller(Featurizer):
    """
    Calls methods from the molecule object using fixed kwargs
    """

    @classmethod
    def get_feature_names(cls, method_map: list[str], **kwargs) -> list[str]:
        method_name_map = {
            # rename common methods to what the output is
            "to_inchi_key": "inchi_key",
            "to_inchi": "inchi",
            "to_smiles": "smiles",
            # !!! maybe just remove "to_" when the str starts with it?
            # for MolecularDataFrame special type:
            "_get_smiles_with_h": "smiles",
        }
        return list(
            [
                (
                    method_name_map.get(k, k)
                    if isinstance(k, str)
                    else method_name_map.get(k.__name__, k.__name__)
                )
                for k in method_map.keys()
            ]
        )

    @staticmethod
    def featurize(
        molecule: Molecule,
        method_map: dict,  # e.g. {"to_inchi_key": {}, "get_fingerprint": {"fingerprint_type": "topological"}}
        **kwargs,
    ) -> numpy.array:
        values = [
            (
                getattr(molecule, method_name)(**method_kwargs)
                if isinstance(method_name, str)
                else method_name(molecule=molecule, **method_kwargs)
            )  # assume callable
            for method_name, method_kwargs in method_map.items()
        ]
        return numpy.array(values)
