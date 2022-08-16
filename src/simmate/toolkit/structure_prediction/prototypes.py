# -*- coding: utf-8 -*-

from simmate.toolkit import Composition, Structure
from simmate.toolkit.creators.structure.prototypes import FromAflowPrototypes


def get_structures_from_prototypes(
    composition: Composition,
    **kwargs,
) -> list[Structure]:
    """
    Generates a list of structures by using prototypes as templates. This function
    is a simple wrapper around the functionality in
    `simmate.toolkit.creators.structures.prototypes`. For more control over the
    structures generated, refer to the underlying creator class.
    """

    from_prototypes = FromAflowPrototypes(
        composition,
        **kwargs,
    ).structures

    return from_prototypes
