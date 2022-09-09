# -*- coding: utf-8 -*-

from pymatgen.analysis.structure_matcher import StructureMatcher

from simmate.toolkit import Composition, Structure
from simmate.toolkit.creators.structure.prototypes import FromAflowPrototypes


def get_structures_from_prototypes(
    composition: Composition,
    remove_matching: bool = True,
    **kwargs,
) -> list[Structure]:
    """
    Generates a list of structures by using prototypes as templates. This function
    is a simple wrapper around the functionality in
    `simmate.toolkit.creators.structures.prototypes`. For more control over the
    structures generated, refer to the underlying creator class.
    """

    structures = FromAflowPrototypes(
        composition,
        **kwargs,
    ).structures

    if remove_matching:
        matcher = StructureMatcher()
        groups = matcher.group_structures(structures)
        # just grab the first result of each group
        structures = [group[0] for group in groups]

    return structures
