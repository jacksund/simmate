# -*- coding: utf-8 -*-

import logging
import time
from pathlib import Path

from simmate.database.workflow_results import FixedCompositionSearch as SearchDatatable
from simmate.toolkit import Composition
from simmate.workflow_engine import Workflow


class StructurePrediction__Python__FixedComposition(Workflow):

    use_database = False
    # consider making a calculation table so that the first step of saving
    # Evolutionary Search is done automatically. It will also ease the
    # tracking of output files when many fixed compositions are submitted.

    @staticmethod
    def run_config(
        composition: str | Composition,
        subworkflow_name: str | Workflow = "relaxation.vasp.staged",
        subworkflow_kwargs: dict = {},
        fitness_field: str = "energy_per_atom",
        max_structures: int = None,
        min_structures_exact: int = None,
        limit_best_survival: int = None,
        convergence_limit: float = 0.001,
        nfirst_generation: int = 15,
        nsteadystate: int = 40,
        singleshot_sources: list[str] = [],
        steadystate_sources: list[tuple[float, str]] = [
            (0.30, "RandomSymStructure"),
            (0.30, "from_ase.Heredity"),
            (0.10, "from_ase.SoftMutation"),
            (0.05, "from_ase.MirrorMutation"),
            (0.05, "from_ase.LatticeStrain"),
            (0.05, "from_ase.RotationalMutation"),
            (0.05, "from_ase.AtomicPermutation"),
            (0.05, "from_ase.CoordinatePerturbation"),
            (0.05, "ExtremeSymmetry"),
        ],
        selector_name: str = "TruncatedSelection",
        selector_kwargs: dict = {},
        validator_name: str = "PartialCrystalNNFingerprint",
        validator_kwargs: dict = {},
        tags: list[str] = None,
        sleep_step: int = 60,
        directory: Path = None,
        write_summary_files: bool = True,
        **kwargs,
    ):
        """
        Sets up the search engine and its settings
        """

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
        # An example would be rerunning substituitions when new structures are available
        #######################################################################

        logging.info(f"Setting up evolutionary search for {composition}")

        # Convergence criteria and stop conditions can be set based on the
        # number of atoms in the composition. Here we try to set reasons criteria
        # for these if a user-input was not given. Note we are using max(..., N)
        # to set an absolute minimum for these.
        n = composition.num_atoms
        min_structures_exact = min_structures_exact or max([int(30 * n), 100])
        max_structures = max_structures or max([int(n * 250 + n**2.75), 1500])
        limit_best_survival = limit_best_survival or max([int(30 * n + n**2), 100])

        #  Add the search entry to the DB.
        search_datatable = SearchDatatable(
            composition=composition.formula,
            subworkflow_name=subworkflow_name,
            subworkflow_kwargs=subworkflow_kwargs,
            fitness_field=fitness_field,
            max_structures=max_structures,
            min_structures_exact=min_structures_exact,
            limit_best_survival=limit_best_survival,
            convergence_limit=convergence_limit,
            nfirst_generation=nfirst_generation,
            nsteadystate=nsteadystate,
            selector_name=selector_name,
            selector_kwargs=selector_kwargs,
            validator_name=validator_name,
            validator_kwargs=validator_kwargs,
            tags=tags,
            sleep_step=sleep_step,
        )
        search_datatable.save()

        if search_datatable.check_stop_condition():
            logging.info("Looks like this search was already ran by someone else!")
            return

        # See if the singleshot sources have been ran yet. For restarted calculations
        # this will likely not be needed (unless a new source was added). But for
        # new searches/compositions, this will submit all individuals from the
        # single shot sources before we even start the steady-state runs
        search_datatable._check_singleshot_sources(directory)

        # Initialize the steady state sources by saving their config information
        # to the database.
        search_datatable._init_steadystate_sources_to_db(steadystate_sources)

        logging.info("Finished setup")
        logging.info(
            f"Assigned this to FixedCompositionSearch id={search_datatable.id}."
        )

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
