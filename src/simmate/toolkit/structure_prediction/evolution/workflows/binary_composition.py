# -*- coding: utf-8 -*-

import itertools
import logging
from pathlib import Path

from rich.progress import track

from simmate.toolkit import Composition
from simmate.toolkit.structure_prediction import (
    get_known_structures,
    get_structures_from_prototypes,
)
from simmate.toolkit.structure_prediction.evolution.workflows.fixed_composition import (
    StructurePrediction__Python__FixedComposition,
)
from simmate.utilities import get_directory
from simmate.workflow_engine import Workflow
from simmate.workflows.utilities import get_workflow

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
        max_atoms: int = 10,
        subworkflow_name: str = "relaxation.vasp.staged",
        subworkflow_kwargs: dict = {},
        # max_stoich_factor: int = 4,
        directory: Path = None,
        singleshot_sources: list[str] = [],
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

        logging.info("Generating input structures from third-party databases")
        structures_known = []
        for composition in track(compositions_maxed):
            new_structures = get_known_structures(
                composition,
                allow_multiples=True,
                nsites__lte=max_atoms,
            )
            structures_known += new_structures
        logging.info(
            f"Generated {len(structures_known)} structures from other databases"
        )

        # sort the structures from fewest nsites to most so that we can submit
        # them in this order.
        structures_known.sort(key=lambda s: s.num_sites)

        # write cif files
        directory_known = get_directory(directory / "known_structures")
        for i, s in enumerate(structures_known):
            s.to("cif", directory_known / f"{i}.cif")

        # and submit them and disable the logs while we submit
        logging.info("Submitting known structures")
        logger = logging.getLogger()
        logger.disabled = True
        for structure in track(structures_known):
            subworkflow.run_cloud(
                structure=structure,
                **subworkflow_kwargs,
            )
        logger.disabled = False

        # ---------------------------------------------------------------------
        # Submitting structures from prototypes
        # ---------------------------------------------------------------------

        # Start by generating the singleshot sources for each factor size.
        logging.info("Generating input structures from prototypes")
        structures_prototype = []
        # for singleshot_source in singleshot_sources: ## TODO
        for composition in track(compositions_maxed):

            # generate all prototypes
            new_structures = get_structures_from_prototypes(
                composition,
                max_sites=max_atoms,
            )
            structures_prototype += new_structures
        logging.info(
            f"Generated {len(structures_prototype)} structures from prototypes"
        )

        # sort the structures from fewest nsites to most so that we can submit
        # them in this order.
        structures_prototype.sort(key=lambda s: s.num_sites)

        directory_sub = get_directory(directory / "from_prototypes")
        for i, s in enumerate(structures_prototype):
            s.to("cif", directory_sub / f"{i}.cif")

        # and submit them and disable the logs while we submit
        logging.info("Submitting prototype structures")
        logger = logging.getLogger()
        logger.disabled = True
        for structure in track(structures_prototype):
            subworkflow.run_cloud(
                structure=structure,
                **subworkflow_kwargs,
            )
        logger.disabled = False

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

            logging.info(f"Beginning compositional searches with natoms = {natoms}")
            current_compositions = [c for c in compositions if c.num_atoms == natoms]

            for composition in current_compositions:

                # OPTIMIZE: Should I just skip single-element compositions?
                # BUG: I do skip these for now because compositions like "N1"
                # are failing in vasp for me.
                if len(composition.elements) == 1:
                    logging.warn(f"Skipping single-element composition {composition}")
                    continue

                # OPTIMIZE: Setting stop conditions for each search will be
                # essential in ensure we don't waste too much calculation time
                # on one composition -- while simultaniously making sure we
                # searched a compositon enough.
                n = composition.num_atoms
                min_structures_exact = int(10 * n)
                limit_best_survival = int(20 * n)
                max_structures = int(30 * n)

                # NOTES: This code below is for printing out the cutoff limits
                # I keep this here for early development as we figure out ideal
                # stopping conditions.
                # for n in range(1, 10):
                #     min_structures_exact = int(10 * n)
                #     limit_best_survival = int(10 * n)
                #     max_structures = int(30 * n)
                #     print(
                #         f"{n}\t{min_structures_exact}\t"
                #         f"{limit_best_survival}\t{max_structures}"
                #     )

                cls.fixed_comp_workflow.run(
                    composition=composition,
                    subworkflow_name=subworkflow_name,
                    subworkflow_kwargs=subworkflow_kwargs,
                    min_structures_exact=min_structures_exact,
                    limit_best_survival=limit_best_survival,
                    max_structures=max_structures,
                    directory=directory / composition.reduced_formula,
                    # Because we submitted all steady states above, we don't
                    # need the other workflows to do these anymore.
                    singleshot_sources=[],
                    # If set to True, then the current fixed composition will be
                    # written to fixed-compositon-logs
                    ###### OPTIMIZE --- set this to false in the future...?
                    # write_summary_files=False,
                )
