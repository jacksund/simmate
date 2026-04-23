# -*- coding: utf-8 -*-

from rich.progress import track

from simmate.toolkit import Molecule
from simmate.toolkit.filters.base import Filter


class RemoveInvalidSmiles(Filter):
    """
    Filters a list of SMILES strings, returning True for valid ones and False
    for invalid ones. It also initializes the `Molecule` objects for valid ones.

    This filter overrides the base class `filter` to allow a custom `return_mode`
    called "molecules_and_booleans" which returns a tuple of both lists.
    """

    is_atomic = False

    @classmethod
    def _check_serial(
        cls,
        molecules: list[str],
        progress_bar: bool = False,
        **kwargs,
    ) -> list:
        """
        Parses a list of SMILES strings in serial.
        Returns a list where valid molecules yield a `Molecule` object,
        and invalid molecules yield `False`.
        """
        features_list = []
        for smiles in track(molecules, disable=not progress_bar):
            try:
                mol = Molecule.from_smiles(smiles)
                features_list.append(mol)
            except Exception:
                features_list.append(False)
        return features_list

    @classmethod
    def filter(
        cls,
        molecules: list[str],
        return_mode: str = "molecules",
        parallel: bool = False,
        **kwargs,
    ) -> list | tuple[list[bool], list[Molecule]]:
        """
        Filters a list of SMILES strings in a serial or parallel manner.
        """
        if not parallel:
            results = cls._check_serial(molecules, **kwargs)
        else:
            results = cls._check_parallel(molecules, **kwargs)

        if return_mode == "count":
            return sum([bool(x) for x in results])
        elif return_mode == "booleans":
            return [bool(x) for x in results]
        elif return_mode == "index":
            return [i for i, keep in enumerate(results) if keep]
        elif return_mode == "molecules":
            return [x for x in results if x]
        elif return_mode == "molecules_and_booleans":
            return [bool(x) for x in results], [x for x in results if x]
        else:
            raise Exception(f"Unknown return mode: {return_mode}")
