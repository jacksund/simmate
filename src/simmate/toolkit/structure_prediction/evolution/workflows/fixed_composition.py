# -*- coding: utf-8 -*-

import logging
import time
from pathlib import Path

from simmate.database.workflow_results import EvolutionarySearch as SearchDatatable
from simmate.toolkit import Composition
from simmate.workflow_engine import Workflow

# TODO
# StructurePrediction__Python__VariableTernaryComposition
#   --> calls VariableBinaryComposition strategically
#   --> might call FixedCompositionVariableNsites strategically too
# StructurePrediction__Python__VariableBinaryComposition
#   --> calls FixedCompositionVariableNsites strategically
# StructurePrediction__Python__FixedCompositionVariableNsites
#   --> calls FixedComposition strategically


class StructurePrediction__Python__FixedComposition(Workflow):

    use_database = False
    # consider making a calculation table so that the first step of saving
    # Evolutionary Search is done automatically. It will also ease the
    # tracking of output files when many fixed compositions are submitted.

    @classmethod
    def run_config(
        cls,
        composition: str | Composition,
        subworkflow_name: str | Workflow = "relaxation.vasp.staged",
        subworkflow_kwargs: dict = {},
        fitness_field: str = "energy_per_atom",
        max_structures: int = 3000,
        limit_best_survival: int = 250,
        nfirst_generation: int = 20,
        nsteadystate: int = 40,
        singleshot_sources: list[str] = [],
        steadystate_sources: list[tuple[float, str]] = [
            (0.30, "RandomSymStructure"),
            (0.30, "from_ase.Heredity"),
            (0.10, "from_ase.SoftMutation"),
            (0.10, "from_ase.MirrorMutation"),
            (0.05, "from_ase.LatticeStrain"),
            (0.05, "from_ase.RotationalMutation"),
            (0.05, "from_ase.AtomicPermutation"),
            (0.05, "from_ase.CoordinatePerturbation"),
        ],
        selector_name: str = "TruncatedSelection",
        selector_kwargs: dict = {},
        validator_name: str = "PartialCrystalNNFingerprint",
        validator_kwargs: dict = {},
        tags: list[str] = None,
        sleep_step: int = 60,
        directory: Path = None,
        **kwargs,
    ):
        """
        Sets up the search engine and its settings.

        #### Parameters

        - `composition`:
            The composition to run the evolutionary search for. Note that the
            number of sites is fixed to what is set here. (Ca2N vs Ca4N2)

        - `workflow`:
            The workflow to run all individuals through. Note, the result_database
            of this workflow will be treated as the individuals in this search.
            The default is "relaxation.vasp.staged"

        - `workflow_command`:
            The command that will be passed to the workflow.run() method.

        - `max_structures`:
            The maximum number of individuals that will be calculated before
            stopping the search. The default is 3000.

        - `limit_best_survival`:
            The search is stopped when the best individual remains unbeaten for
            this number of new individuals. The default is 250.

        - `singleshot_sources`:
            TODO: This is not implemented yet

        - `nfirst_generation`:
            No mutations or "child" individuals will be carried out until this
            number of individuals have been calculated. The default is 20.

        - `nsteadystate`:
            The total number of individuals from steady-state sources that will
            be running/submitted at any given time. The default is 40.

        - `steadystate_sources`:
            A list of tuples where each tuple is (percent, source). The percent
            determines the number of steady stage calculations that will be
            running for this at any given time. For example, 0.25 means
            0.25*40=10 individuals will be running/submitted at all times. The
            source can be from either the toolkit.creator or toolkit.transformations
            modules. Don't change this default unless you know what you're doing!

        - `selector`:
            The defualt method to use for choosing the parent individual(s). The
            default is TruncatedSelection.
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
        # TODO: Should I add logs to inform how the workflow will be ran? Or
        # leave it to the simmate_metadata.yaml file and database for this?
        # logging.info(f"Individuals will be evaulated using '{subworkflow_name}'")
        # logging.info(f"Parent selection for mutations will use '{selector_name}'")

        #  Add the search entry to the DB.
        search_datatable = SearchDatatable(
            composition=composition.formula,
            subworkflow_name=subworkflow_name,
            subworkflow_kwargs=subworkflow_kwargs,
            fitness_field=fitness_field,
            max_structures=max_structures,
            limit_best_survival=limit_best_survival,
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
        logging.info(f"Assigned this to EvolutionarySearch id={search_datatable.id}.")

        # this loop will go until I hit 'break' below
        while True:

            # Write the output summary if there is at least one structure completed
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
