# -*- coding: utf-8 -*-

from typing import List

from simmate.toolkit import Composition, Structure
from simmate.toolkit.creators.structure.prototypes import FromAflowPrototypes


def get_structures_from_prototypes(
    composition: Composition,
) -> List[Structure]:
    """
    Generates a list of structures by using prototypes as template. This function
    is a simple wrapper around the functionality in
    `simmate.toolkit.creators.structures.prototypes`. For more control over the
    structures generated, refer to this underlying creator class.
    """

    # generate input structures using all methods supported by the base class
    from_ordered = FromAflowPrototypes(
        composition,
        mode="ordered",
        allow_multiples=True,
    )
    from_exact = FromAflowPrototypes(
        composition,
        mode="exact",
    )

    # go through both list results and remove duplicate structures
    unique_structures = []
    for structure in from_ordered.structures + from_exact.structures:
        if structure not in unique_structures:
            unique_structures.append(structure)

    return unique_structures
