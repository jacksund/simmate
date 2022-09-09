# -*- coding: utf-8 -*-

import logging
import time
from pathlib import Path

from simmate.database.workflow_results import FixedCompositionSearch
from simmate.toolkit import Composition
from simmate.workflow_engine import Workflow


class StructurePrediction__Toolkit__FixedComposition(Workflow):
    """
    Runs an evolutionary search algorithm on a fixed composition with a fixed
    number of sites. (e.g. Ca2N or Na4Cl4)
    """

    database_table = FixedCompositionSearch

    @classmethod
    def run_config(
        cls,
        composition: str | Composition,
        subworkflow_name: str | Workflow = "relaxation.vasp.staged",
        subworkflow_kwargs: dict = {},
        fitness_field: str = "energy_per_atom",
        max_structures: int = None,
        min_structures_exact: int = None,
        best_survival_cutoff: int = None,
        convergence_cutoff: float = 0.001,
        nfirst_generation: int = 15,
        nsteadystate: int = 40,
        singleshot_sources: list[str] = [
            "third_parties",
            "prototypes",
            # "third_party_substituition",
        ],
        steadystate_sources: dict = {
            "RandomSymStructure": 0.60,
            "from_ase.Heredity": 0.25,
            # "from_ase.SoftMutation": 0.10,
            "from_ase.MirrorMutation": 0.05,
            # "from_ase.LatticeStrain": 0.05,
            "from_ase.RotationalMutation": 0.05,
            "from_ase.AtomicPermutation": 0.05,
            # "from_ase.CoordinatePerturbation": 0.05,
            # "ExtremeSymmetry": 0.05,
        },
        selector_name: str = "TruncatedSelection",
        selector_kwargs: dict = {},
        validator_name: str = "PartialRdfFingerprint",
        validator_kwargs: dict = {
            "distance_tolerance": 0.001,
            "cutoff": 10.0,
            "bin_size": 0.1,
        },
        sleep_step: int = 60,
        directory: Path = None,
        write_summary_files: bool = True,
        run_id: str = None,
        **kwargs,
    ):

        #######################################################################
        # TODO: Check if there is an existing search and grab it if so.
        # We can also update, add logs, compare... I need to decide what to do
        # here. The stop condition could also be checked to see if a search
        # even needs to be started.
        # if SearchDatatable.objects.filter(composition=composition.formula).exists():
        #     self.search_datatable = SearchDatatable.objects.filter(
        #         composition=composition.formula,
        #     ).get()
        # Grab the list of singleshot sources that have been ran before
        # and based off of that list, remove repeated sources
        # past_singleshot_sources = (
        #     self.search_datatable.sources.filter(is_singleshot=True)
        #     .values_list("name", flat=True)
        #     .all()
        # )
        # singleshot_sources = [
        #     source
        #     for source in singleshot_sources
        #     if source not in past_singleshot_sources
        # ]
        # BUG: what if I want to rerun any of these even though its been ran before?
        #######################################################################

        logging.info(f"Setting up evolutionary search for {composition}")

        # grab the calculation table linked to this workflow run
        search_datatable = cls.database_table.objects.get(run_id=run_id)

        # Convergence criteria and stop conditions can be set based on the
        # number of atoms in the composition. Here we try to set reasonable criteria
        # for these if a user-input was not given. Note we are using max(..., N)
        # to set an absolute minimum for these.
        n = composition.num_atoms
        min_structures_exact = min_structures_exact or max([int(30 * n), 100])
        max_structures = max_structures or max([int(n * 250 + n**2.75), 1500])
        best_survival_cutoff = best_survival_cutoff or max([int(30 * n + n**2), 100])
        search_datatable.update_from_fields(
            min_structures_exact=min_structures_exact,
            max_structures=max_structures,
            best_survival_cutoff=best_survival_cutoff,
        )

        # sometimes the conditions are already met by a previous search so we
        # check for this up front.
        if search_datatable.check_stop_condition():
            logging.info("Looks like this search was already ran by someone else!")
            return

        logging.info("Finished setup")
        logging.info(
            f"Assigned this to FixedCompositionSearch id={search_datatable.id}."
        )

        # See if the singleshot sources have been ran yet. For restarted calculations
        # this will likely not be needed (unless a new source was added). But for
        # new searches/compositions, this will submit all individuals from the
        # single shot sources before we even start the steady-state runs
        search_datatable._check_singleshot_sources(directory)

        # this loop will go until I hit 'break' below
        while True:

            # Write the output summary if there is at least one structure completed
            if write_summary_files:
                if search_datatable.individuals_completed.count() >= 1:
                    search_datatable.write_summary(directory)
                else:
                    search_datatable.write_individuals_incomplete(directory)

            # TODO: maybe write summary files to csv...? This may be a mute
            # point because I expect we can follow along in the web UI in the future
            # To that end, I can add a "URL" property

            # Check the stop condition
            # If it is True, we can stop the calc.
            if search_datatable.check_stop_condition():
                # TODO: should I sleep / wait for other calculations and
                # check again? Then write summary one last time..?
                break  # break out of the while loop
            # Otherwise, keep going!

            # TODO: Go through triggered actions that would update the database
            # table -- e.g. the workflow to run, the validators, etc.
            # self._check_triggered_actions()

            # Go through the running workflows and see if we need to submit
            # new ones to meet our steadystate target(s)
            search_datatable._check_steadystate_workflows()

            # To save our database load, sleep until we run checks again.
            logging.info(
                f"Sleeping for {sleep_step} seconds before running checks again."
            )
            time.sleep(sleep_step)

        logging.info("Stopping the search (running calcs will be left to finish).")
