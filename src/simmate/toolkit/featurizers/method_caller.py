from simmate.toolkit import Molecule

from .base import Featurizer


class MethodCaller(Featurizer):
    """
    Calls methods from the molecule object using fixed kwargs.

    Methods can be chained with dots (e.g. "get_flattened.to_smiles"), where
    all but the last method are called without kwargs. If a chained method
    works in-place and returns None (e.g. "add_hydrogens.to_smiles"), the chain
    continues with the same (now modified) molecule.
    """

    @classmethod
    def get_feature_names(cls, method_map: list[str], **kwargs) -> list[str]:
        method_name_map = {
            # rename common methods to what the output is
            "to_inchi_key": "inchi_key",
            "to_inchi": "inchi",
            "to_smiles": "smiles",
            "get_flattened.to_smiles": "flat_smiles",
            # !!! maybe just remove "to_" when the str starts with it?
            # for MolecularDataFrame special type:
            "add_hydrogens.to_smiles": "smiles",
        }
        return [
            (
                method_name_map.get(k, k)
                if isinstance(k, str)
                else method_name_map.get(k.__name__, k.__name__)
            )
            for k in method_map
        ]

    @staticmethod
    def featurize(
        molecule: Molecule,
        method_map: dict,  # e.g. {"to_inchi_key": {}, "get_fingerprint": {"fingerprint_type": "topological"}}
        **kwargs,
    ) -> list:
        # a plain list, so values of mixed types keep their own types
        values = []
        for method_name, method_kwargs in method_map.items():
            if not isinstance(method_name, str):  # assume callable
                values.append(method_name(molecule=molecule, **method_kwargs))
                continue
            *chained_names, final_name = method_name.split(".")
            obj = molecule
            for name in chained_names:
                result = getattr(obj, name)()
                obj = obj if result is None else result
            values.append(getattr(obj, final_name)(**method_kwargs))
        return values
