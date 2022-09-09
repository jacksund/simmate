# -*- coding: utf-8 -*-

import itertools
import logging
from pathlib import Path

from rich.progress import track

from simmate.toolkit import Composition
from simmate.toolkit.structure_prediction.evolution.database.binary_system import (
    BinarySystemSearch,
)
from simmate.toolkit.structure_prediction.evolution.workflows.fixed_composition import (
    StructurePrediction__Toolkit__FixedComposition,
)
from simmate.toolkit.structure_prediction.evolution.workflows.utilities import (
    write_and_submit_structures,
)
from simmate.toolkit.structure_prediction.known import get_known_structures
from simmate.toolkit.structure_prediction.prototypes import (
    get_structures_from_prototypes,
)
from simmate.workflow_engine import Workflow
from simmate.workflows.utilities import get_workflow


class StructurePrediction__Toolkit__BinarySystem(Workflow):
    """
    Runs an evolutionary search algorithm to predict the most stable structures
    of a binary phase system (e.g Na-Cl or Y-C)
    """

    database_table = BinarySystemSearch

    fixed_comp_workflow = StructurePrediction__Toolkit__FixedComposition

    @classmethod
    def run_config(
        cls,
        chemical_system: str,
        max_atoms: int = 10,
        subworkflow_name: str = "relaxation.vasp.staged",
        subworkflow_kwargs: dict = {},
        max_stoich_factor: int = 4,
        directory: Path = None,
        singleshot_sources: list[str] = [
            "third_parties",
            "prototypes",
        ],
        **kwargs,  # passed to fixed_comp_workflow
    ):

        # ---------------------------------------------------------------------
        # Setting up
        # ---------------------------------------------------------------------

        subworkflow = get_workflow(subworkflow_name)

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
        logging.info(f"{len(compositions)} unique compositions will be explored")

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

        if "third_parties" in singleshot_sources:

            logging.info("Generating input structures from third-party databases")
            structures_known = []
            for composition in track(compositions_maxed):
                new_structures = get_known_structures(
                    composition,
                    allow_multiples=True,
                    remove_matching=True,
                    nsites__lte=max_atoms,
                )
                structures_known += new_structures
            logging.info(
                f"Generated {len(structures_known)} structures from other databases"
            )
            write_and_submit_structures(
                structures=structures_known,
                foldername=directory / "from_third_parties",
                workflow=subworkflow,
                workflow_kwargs=subworkflow_kwargs,
            )

        # ---------------------------------------------------------------------
        # Submitting structures from prototypes
        # ---------------------------------------------------------------------

        if "prototypes" in singleshot_sources:

            # Start by generating the singleshot sources for each factor size.
            logging.info("Generating input structures from prototypes")
            structures_prototype = []
            # for singleshot_source in singleshot_sources: ## TODO
            for composition in track(compositions_maxed):

                # generate all prototypes
                new_structures = get_structures_from_prototypes(
                    composition,
                    max_sites=max_atoms,
                    remove_matching=True,
                )
                structures_prototype += new_structures
            logging.info(
                f"Generated {len(structures_prototype)} structures from prototypes"
            )
            write_and_submit_structures(
                structures=structures_prototype,
                foldername=directory / "from_prototypes",
                workflow=subworkflow,
                workflow_kwargs=subworkflow_kwargs,
            )

        # ---------------------------------------------------------------------
        # Starting search
        # ---------------------------------------------------------------------

        # Now we are going to cycle through factor sizes, starting at the lowest
        # and working our way up. We do this because:
        #   1. smaller unitcells run much faster (for DFT-calculation)
        #   2. smaller compositions converge much faster (for number of
        #       calcs required)
        #   3. results from smaller unitcells can help to speed up the larger
        #       compositional searches.

        for natoms in range(1, max_atoms + 1):

            # for stage_number in range(1, 4) --> consider adding substages

            # Setting stop conditions for each search will be
            # essential in ensure we don't waste too much calculation time
            # on one composition -- while simultaniously making sure we
            # searched a compositon enough.
            min_structures_exact = int(5 * natoms)
            best_survival_cutoff = int(20 * natoms)
            max_structures = int(30 * natoms)
            convergence_cutoff = 0.01  # 10 meV as looser convergence limit

            # OPTIMIZE: This code below is for printing out the cutoff limits
            # I keep this here for early development as we figure out ideal
            # stopping conditions.
            # for n in range(1, 10):
            #     min_structures_exact = int(5 * n)
            #     best_survival_cutoff = int(10 * n)
            #     max_structures = int(25 * n)
            #     # convergence_cutoff = 0.01
            #     print(
            #         f"{n}\t{min_structures_exact}\t"
            #         f"{best_survival_cutoff}\t{max_structures}"
            #         # f"\t{convergence_cutoff}"
            #     )

            logging.info(f"Beginning compositional searches with natoms = {natoms}")
            current_compositions = [c for c in compositions if c.num_atoms == natoms]

            for composition in current_compositions:

                # OPTIMIZE: Should I just skip single-element compositions?
                # BUG: I do skip these for now because compositions like "N1"
                # are failing in vasp for me.
                if len(composition.elements) == 1:
                    logging.warn(f"Skipping single-element composition {composition}")
                    continue

                # For this first cycle, we only look at non-reduced compositions
                # up to the max_stoich_factor. This means Ca2N and max factor
                # of 4 would only look up to Ca8N4 and skip any compositions
                # with more atoms.
                current_factor = int(
                    composition.reduced_composition.num_atoms / composition.num_atoms
                )
                if current_factor > max_stoich_factor:
                    logging.warn(
                        f"Skipping composition {composition} bc it exceeds the max "
                        f"factor of {max_stoich_factor}"
                    )
                    continue

                # If we pass the checks above, we can start the new fixed-composition
                # search for this composition
                cls.fixed_comp_workflow.run(
                    composition=composition,
                    subworkflow_name=subworkflow_name,
                    subworkflow_kwargs=subworkflow_kwargs,
                    min_structures_exact=min_structures_exact,
                    best_survival_cutoff=best_survival_cutoff,
                    max_structures=max_structures,
                    directory=directory / composition.reduced_formula,
                    convergence_cutoff=convergence_cutoff,
                    # Because we submitted all steady states above, we don't
                    # need the other workflows to do these anymore.
                    singleshot_sources=[],
                    # If set to True, then the current fixed composition will be
                    # written to fixed-compositon-logs
                    ###### OPTIMIZE --- set this to false in the future...?
                    # write_summary_files=False,
                )
