# -*- coding: utf-8 -*-

from simmate.toolkit import Molecule
from simmate.toolkit.filters.base import Filter


class ManySmarts(Filter):
    # This class can be considered a refactor from RDkit:
    # https://github.com/rdkit/rdkit/blob/master/rdkit/VLib/NodeLib/SmartsMolFilter.py

    is_atomic = True

    @classmethod
    def check(
        cls,
        molecule: Molecule,
        smarts_list: list[Molecule],
    ) -> bool:
        # TODO: This will likely become a Molecule method in the future
        # TODO: should this be an ANY or ALL clause? Or maybe an input kwarg?
        for smarts in smarts_list:
            # molecule.rdkit_molecule.GetSubstructMatches(smarts)
            if molecule.rdkit_molecule.HasSubstructMatch(smarts):
                return True
        # It's false if we make it through the entire loop above
        return False
