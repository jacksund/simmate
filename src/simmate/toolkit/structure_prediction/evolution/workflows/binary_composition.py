# -*- coding: utf-8 -*-

import logging
from pathlib import Path
import itertools

from rich.progress import track

from simmate.toolkit import Composition
from simmate.toolkit.structure_prediction.evolution.workflows.fixed_composition import (
    StructurePrediction__Python__FixedComposition,
)
from simmate.workflow_engine import Workflow
from simmate.toolkit.structure_prediction import (
    get_known_structures,
    get_structures_from_prototypes,
)
from simmate.utilities import get_directory

# TODO
# StructurePrediction__Python__VariableTernaryComposition
#   --> calls VariableBinaryComposition strategically
#   --> might call FixedCompositionVariableNsites strategically too


class StructurePrediction__Python__BinaryComposition(Workflow):

    use_database = False

    fixed_comp_workflow = StructurePrediction__Python__FixedComposition

    @classmethod
    def run_config(
        cls,
        chemical_system: str,
        max_sites: int = 20,
        # max_stoich_factor: int = 4,
        directory: Path = None,
        singleshot_sources: list[str] = [],
        **kwargs,  # passed to fixed_comp_workflow
    ):

        print("REMOVE ME!")
        chemical_system = "Ca-N"
        max_atoms = 20

        # ---------------------------------------------------------------------
        # Setting up
        # ---------------------------------------------------------------------

        # Grab the two elements that we are working with. Also if this raises
        # an error, we want to provide useful feedback to the user
        try:
            element_1, element_2 = chemical_system.split("-")
        except:
            raise Exception(
                "Failed to split {} into elements. Your format for the input "
                "chemical system should be two elements and follow the format "
                "Element1-Element2. Ex: Na-Cl, Ca-N, Y-C, etc."
            )

        # Find all unique compositions
        compositions = []
        for nsites in range(1, max_atoms + 1):
            for combo in itertools.combinations_with_replacement(
                [element_1, element_2], nsites
            ):

                composition = Composition(
                    {
                        element_1: combo.count(element_1),
                        element_2: combo.count(element_2),
                    }
                )

                compositions.append(composition)
        logging.info(
            f"{len(compositions)} unique compositions will be explored"
        )

        # now condense this list down to just the reduced formulas
        compositions_reduced = []
        for composition in compositions:
            reduced = composition.reduced_composition
            if reduced not in compositions_reduced:
                compositions_reduced.append(reduced)
        logging.info(
            f"This corresponds to {len(compositions_reduced)} reduced compositions"
        )

        # it is also useful to store the "max compositions". This the composition
        # for when the max number of possible sites are used. For example,
        # Ca2N with max atoms of 20 would give a max composition of Ca12N6 (18 atoms).
        # We make this list using only the reduced compositions as input.
        compositions_maxed = []
        for composition in compositions_reduced:
            max_factor = int(max_atoms // composition.num_atoms)
            # BUG: we need to call Composition() to convert the pymatgen
            # object back into a simmate composition.
            max_composition = Composition(max_factor * composition)

            if max_composition not in compositions_maxed:
                compositions_maxed.append(max_composition)

        # ---------------------------------------------------------------------
        # Submitting known structures
        # ---------------------------------------------------------------------

        logging.info("Generating input structures from third-party databases")
        structures = []
        for composition in track(compositions_maxed):

            structures_known = get_known_structures(
                composition,
                allow_multiples=True,
                nsites__lte=max_atoms,
            )
            logging.info(
                f"Generated {len(structures_known)} structures from other databases"
            )
            structures += structures_known

        # sort the structures from fewest nsites to most so that we can submit
        # them in this order.
        structures_known.sort(key=lambda s: s.num_sites)

        directory_known = get_directory(directory / "known_structures")
        for i, s in enumerate(structures_known):
            s.to("cif", directory_known / f"{i}.cif")

        # ---------------------------------------------------------------------
        # Submitting structures from prototypes
        # ---------------------------------------------------------------------

        # Start by generating the singleshot sources for each factor size.
        logging.info("Generating input structures from prototypes")
        structures = []
        # for singleshot_source in singleshot_sources: ## TODO
        for composition in track(compositions_maxed):

            # generate all prototypes
            structures_prototype = get_structures_from_prototypes(
                composition,
                max_sites=max_atoms,
            )
            structures += structures_prototype
        logging.info(f"Generated {len(structures)} structures from prototypes")

        # sort the structures from fewest nsites to most so that we can submit
        # them in this order.
        structures.sort(key=lambda s: s.num_sites)

        directory_sub = get_directory(directory / "from_prototypes")
        for i, s in enumerate(structures_prototype):
            s.to("cif", directory_sub / f"{i}.cif")

        # ---------------------------------------------------------------------
        # Starting search
        # ---------------------------------------------------------------------

        # # Now we are going to cycle through factor sizes, starting at the lowest
        # # and working our way up. We do this because:
        # #   1. smaller unitcells run much faster (for DFT-calculation)
        # #   2. smaller compositions converge much faster (for number of
        # #       calcs required)
        # #   3. results from smaller unitcells can help to speed up the larger
        # #       compositional searches.

        # # The search with involve N steps based on the reduced composition.
        # # For example, Ca6N3 would have a reduced comp of Ca2N and max factor
        # # of 3.
        # composition_reduced = composition.reduced_composition
        # max_factor = int(composition.num_atoms / composition_reduced.num_atoms)

        # # Starting at 1, go through each composition step and run a individual
        # # fixed_comp_workflow for that composition.
        # for factor in range(1, max_factor + 1):

        #     composition_current = composition_reduced * factor

        #     # logging.info(f"Beginning composition {composition_current}")
        #     cls.fixed_comp_workflow.run(
        #         composition=composition_current,
        #         # we keep the same base directory as we don't mind files overwriting
        #         # eachother as the search progresses through each factor
        #         directory=directory,
        #         # Because we submitted all steady states above, we don't
        #         # need the other workflows to do these anymore.
        #         singleshot_sources=[],
        #         **kwargs,
        #     )

        #     # logging.info(f"Completed composition {composition_current}")
