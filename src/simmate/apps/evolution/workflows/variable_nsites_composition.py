# -*- coding: utf-8 -*-

import logging
from pathlib import Path

from simmate.apps.evolution.models.variable_nsites_composition import (
    VariableNsitesCompositionSearch,
)
from simmate.apps.evolution.workflows.fixed_composition import (
    StructurePrediction__Toolkit__FixedComposition,
)
from simmate.toolkit import Composition
from simmate.workflows import Workflow


class StructurePrediction__Toolkit__VariableNsitesComposition(Workflow):
    """
    Runs an evolutionary search algorithm to predict the most stable structure
    of a specific composition but with variable number of sites in the unitcell.

    For example, this would be Ca2N and up to 12 atoms (Ca8N4).
    """

    description_doc_short = "variable number of sites (e.g. Ca2N through Ca8N4)"

    database_table = VariableNsitesCompositionSearch

    fixed_comp_workflow = StructurePrediction__Toolkit__FixedComposition

    @classmethod
    def run_config(
        cls,
        composition: str | Composition,
        directory: Path = None,
        singleshot_sources: list[str] = [],
        **kwargs,  # passed to fixed_comp_workflow
    ):
        # Start by submitting the singleshot sources for each factor size.
        logging.warning("Single-shot sources are not implemented yet")

        # Now we are going to cycle through factor sizes, starting at the lowest
        # and working our way up. We do this because:
        #   1. smaller unitcells run much faster (for DFT-calculation)
        #   2. smaller compositions converge much faster (for number of
        #       calcs required)
        #   3. results from smaller unitcells can help to speed up the larger
        #       compositional searches.

        # The search will involve N steps, where N is based on the reduced
        # composition. For example, Ca6N3 would have a reduced comp of Ca2N
        # and max factor of 3.
        composition_reduced = composition.reduced_composition
        max_factor = int(composition.num_atoms / composition_reduced.num_atoms)

        # Starting at 1, go through each composition step and run a individual
        # fixed_comp_workflow for that composition.
        for factor in range(1, max_factor + 1):
            composition_current = composition_reduced * factor

            # BUG: The workflow.run method for this parent workflow will add a
            # started_at kwarg which will cause a multiple keywords error. I
            # just remove the started_at kwarg here, but this could also be fixed
            # by changing to fixed_composition_kwargs = {} or by adding a check
            # for this to the Workflow class itself.
            if "started_at" in kwargs.keys():
                del kwargs["started_at"]

            # logging.info(f"Beginning composition {composition_current}")
            cls.fixed_comp_workflow.run(
                composition=composition_current,
                # we keep the same base directory as we don't mind files overwriting
                # eachother as the search progresses through each factor
                directory=directory,
                # Because we submitted all steady states above, we don't
                # need the other workflows to do these anymore.
                singleshot_sources=[],
                **kwargs,
            )

            # logging.info(f"Completed composition {composition_current}")
