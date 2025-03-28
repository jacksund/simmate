# -*- coding: utf-8 -*-

# isort: skip_file
from simmate.database import connect  # must be first

from pymatgen.analysis.structure_matcher import StructureMatcher

from simmate.apps.aflow.models import AflowStructure
from simmate.apps.cod.models import CodStructure
from simmate.apps.jarvis.models import JarvisStructure
from simmate.apps.materials_project.models import MatprojStructure
from simmate.apps.oqmd.models import OqmdStructure
from simmate.toolkit import Composition, Structure


def get_known_structures(
    composition: Composition,
    allow_multiples: bool = False,
    remove_matching: bool = False,
    **kwargs,  # Extra filtering criteria
) -> list[Structure]:
    """
    Goes through all database tables from default third-party apps
    and grabs all structures with a matching composition.

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
        if not allow_multiples:
            search_results = database_table.objects.filter(
                formula_full=composition.formula,
                **kwargs,
            )
        else:
            search_results = database_table.objects.filter(
                formula_reduced=composition.reduced_formula,
                **kwargs,
            )

        # Convert to toolkit structures so that users can run analyses
        structures += search_results.to_toolkit()

    if remove_matching:
        matcher = StructureMatcher()
        groups = matcher.group_structures(structures)
        structures = [group[0] for group in groups]

    return structures
