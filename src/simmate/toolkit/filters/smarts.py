# -*- coding: utf-8 -*-

from simmate.toolkit import Molecule

from .base import Filter


class ManySmarts(Filter):
    # This class can be considered a refactor from RDkit:
    # https://github.com/rdkit/rdkit/blob/master/rdkit/VLib/NodeLib/SmartsMolFilter.py

    is_atomic = True

    @classmethod
    def check(
        cls,
        molecule: Molecule,
        smarts_list: list[Molecule],
        mode: str = "all",
    ) -> bool:

        if mode == "any":
            # gives True if *any* smarts in the list match the molecule
            for smarts in smarts_list:
                if molecule.is_smarts_match(smarts):
                    return True
            return False

        elif mode == "all":
            # gives True only if *all* smarts in the list match the molecule
            for smarts in smarts_list:
                if not molecule.is_smarts_match(smarts):
                    return False
            return True
