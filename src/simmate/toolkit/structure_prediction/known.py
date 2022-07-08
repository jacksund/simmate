# -*- coding: utf-8 -*-

from typing import List

from simmate.toolkit import Composition, Structure
from simmate.database import connect
from simmate.database.third_parties import (
    AflowStructure,
    CodStructure,
    JarvisStructure,
    MatprojStructure,
    OqmdStructure,
)


def get_known_structures(
    composition: Composition,
    strict_nsites: bool = False,
) -> List[Structure]:
    """
    Goes through all database tables in the `simmate.database.third_parties`
    module and grabs all structures with a matching composition.

    Each database table must be populated -- otherwise this function will
    return an empty list.
    """

    databases_to_search = [
        AflowStructure,
        CodStructure,
        JarvisStructure,
        MatprojStructure,
        OqmdStructure,
    ]

    structures = []

    for database_table in databases_to_search:

        # If there is a limit to nsites, we want to match the composition formula
        # exactly. Otherwise we can match the reduced formula.
        if strict_nsites:
            search_results = database_table.objects.filter(
                formula_full=composition.formula,
            )
        else:
            search_results = database_table.objects.filter(
                formula_reduced=composition.reduced_formula,
            )

        # Convert to toolkit structures so that users can run analyses
        structures += search_results.to_toolkit()

    return structures
