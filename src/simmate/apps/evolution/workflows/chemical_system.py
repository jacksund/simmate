# -*- coding: utf-8 -*-

import itertools
import logging
import time
from pathlib import Path

import numpy
from pymatgen.analysis.reaction_calculator import Reaction, ReactionError
from rich.progress import track

from simmate.apps.evolution.models.chemical_system import ChemicalSystemSearch
from simmate.apps.evolution.singleshot_sources.known import get_known_structures
from simmate.apps.evolution.singleshot_sources.prototypes import (
    get_structures_from_prototypes,
)
from simmate.apps.evolution.workflows.fixed_composition import (
    StructurePrediction__Toolkit__FixedComposition,
)
from simmate.apps.evolution.workflows.utilities import write_and_submit_structures
from simmate.engine import Workflow
from simmate.toolkit import Composition
from simmate.workflows.utilities import get_workflow


class StructurePrediction__Toolkit__ChemicalSystem(Workflow):
    """
    Runs an evolutionary search algorithm to predict the most stable structures
    of a binary phase system (e.g Na-Cl or Y-C)
    """

    description_doc_short = "hull diagram for a two-element system (e.g. Na-Cl)"

    database_table = ChemicalSystemSearch

    fixed_comp_workflow = StructurePrediction__Toolkit__FixedComposition

    @classmethod
    def run_config(
        cls,
        chemical_system: str,
        max_atoms: int = 10,
        subworkflow_name: str = "relaxation.vasp.staged",
        subworkflow_kwargs: dict = {},
        max_stoich_factor: int = 4,
        nfirst_generation: int = 15,
        nsteadystate: int = 40,
        sleep_step: float = 300,
        directory: Path = None,
        singleshot_sources: list[str] = [
            "third_parties",
            "prototypes",
        ],
        run_id: str = None,
        **kwargs,
    ):
        # ---------------------------------------------------------------------
        # Setting up
        # ---------------------------------------------------------------------

        # grab the calculation table linked to this workflow run
        search_datatable = cls.database_table.objects.get(run_id=run_id)

        subworkflow = get_workflow(subworkflow_name)

        # Grab the two elements that we are working with. Also if this raises
        # an error, we want to provide useful feedback to the user
        try:
            endpoint_compositions = [
                Composition(sys) for sys in chemical_system.split("-")
            ]
        except:
            raise Exception(
                "Failed to split {} into elements. Your format for the input "
                "chemical system should be two elements and follow the format "
                "Element1-Element2. Ex: Na-Cl, Ca-N, Y-C, etc."
            )

        # grab all unique elements
        elements = []
        for comp in endpoint_compositions:
            for element in comp.elements:
                if element not in elements:
                    elements.append(element)

        # Find all unique compositions for the list of elements.
        # Note, for complex compositions, this will contain extra compositions
        # that we will want removed. This is addressed in the next step.
        compositions = []
        for nsites in range(1, max_atoms + 1):
            for combo in itertools.combinations_with_replacement(elements, nsites):
                counts = {e.symbol: combo.count(e) for e in elements}
                composition = Composition(**counts)
                compositions.append(composition)

        # For complex chemical systems (e.g. the Sc2C-Sc2CF2 or Y6S4-YF3-Y systems)
        # we need to make sure the composition is contained with that system.
        # The general rule is that it must be possible to stoichiometrically
        # balance the reaction of endpoint compositions with the composition
        # being considered. For example, in the Y6S4-YF3-Y system,
        # Y2SF would be accepted (0.5 Y3S2 + 0.33 YF3 + 0.166 Y -> Y2SF)
        # while YSF would be rejected (0.5 Y3S2 + 0.33 YF3 - 0.833 Y ->  + YSF)
        # (for YSF, note the negative sign for Y)
        compositions_cleaned = []
        for composition in compositions:
            try:
                reaction = Reaction(
                    reactants=endpoint_compositions,
                    products=[composition],
                )
            except ReactionError:
                # reaction could not be balanced and is therefore invalid
                continue

            # iterate and make sure our target composition is close to 1 while
            # all other products are close to 0. Note the is-close checks
            # are because of rounding bugs in the pymatgen code
            is_valid = True
            for product in reaction.products:
                coeff = reaction.get_coeff(product)
                if product == composition and not numpy.isclose(coeff, 1):
                    is_valid = False
                elif product != composition and not numpy.isclose(coeff, 0):
                    is_valid = False
            if is_valid:
                compositions_cleaned.append(composition)
        compositions = compositions_cleaned

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
            states_known = write_and_submit_structures(
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
            states_prototype = write_and_submit_structures(
                structures=structures_prototype,
                foldername=directory / "from_prototypes",
                workflow=subworkflow,
                workflow_kwargs=subworkflow_kwargs,
            )

        # ---------------------------------------------------------------------
        # Wait for singlshot submissions if there are many of them
        # ---------------------------------------------------------------------

        all_submissions = states_prototype + states_known
        if len(all_submissions) > (nsteadystate * 2):
            number_to_wait_for = len(all_submissions) - nsteadystate - 20
            number_to_resume_on = nsteadystate + 20
            logging.info(
                f"Waiting for at least {number_to_wait_for} singleshot "
                "submissions to finish."
            )
            done_waiting = False
            while not done_waiting:
                # go through submitted calculations and count the number of pending
                # calculations
                total_pending = 0
                for state in all_submissions:
                    if state.is_pending():
                        total_pending += 1
                    # we don't need to check past our number_to_wait_for so exiting
                    # this loop saves on database load
                    if total_pending > number_to_resume_on:
                        break

                # check if we exited the loop above with less pending than needed
                if total_pending <= number_to_resume_on:
                    done_waiting = True  # exits while loop

                # sleep before checking again to save on database hits
                time.sleep(sleep_step)

        search_datatable.write_output_summary(directory)

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
            max_structures = int(40 * natoms)
            convergence_cutoff = 0.01  # 10 meV as looser convergence limit

            # OPTIMIZE: This code below is for printing out the cutoff limits
            # I keep this here for early development as we figure out ideal
            # stopping conditions.
            # for n in range(1, 20):
            #     min_structures_exact = int(5 * n)
            #     best_survival_cutoff = int(20 * n)
            #     max_structures = int(40 * n)
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
                    nfirst_generation=nfirst_generation,
                    nsteadystate=nsteadystate,
                    sleep_step=sleep_step,
                    # Because we submitted all steady states above, we don't
                    # need the other workflows to do these anymore.
                    singleshot_sources=[],
                )

                # after each fixed-composition, we can reevaluate the hull diagram
                search_datatable.write_output_summary(directory)
