# -*- coding: utf-8 -*-

import time
from typing import Union
import logging

from simmate.toolkit import Composition
from simmate.workflow_engine import Workflow
from simmate.database.workflow_results import (
    EvolutionarySearch as SearchDatatable,
    StructureSource as SourceDatatable,
)


# TODO

# These should call FixedCompositionVariableNsites strategically
# StructurePrediction__Python__VariableTernaryComposition
# StructurePrediction__Python__VariableBinaryComposition

# This should call FixedComposition strategically
# StructurePrediction__Python__FixedCompositionVariableNsites


class StructurePrediction__Python__FixedComposition(Workflow):

    use_database = False

    @classmethod
    def run_config(
        composition: Union[str, Composition],
        workflow_name: Union[str, Workflow] = "relaxation.vasp.staged",
        workflow_command: str = None,
        max_structures: int = 3000,
        limit_best_survival: int = 250,
        singleshot_sources: list[str] = [],
        nfirst_generation: int = 20,
        nsteadystate: int = 40,
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
        selector: str = "TruncatedSelection",
        tags: list[str] = None,
        # TODO: maybe use **workflow_run_kwargs...?
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

        # make sure we were givent a Composition object, and if not, we have
        # a string that should be converted to one.
        if not isinstance(composition, Composition):
            composition = Composition(composition)
        logging.info(f"Setting up evolutionary search for {composition}")

        self.composition = composition
        self.workflow_command = workflow_command
        self.tags = tags

        # TODO: consider grabbing these from the database so that we can update
        # them at any point.
        self.limit_best_survival = limit_best_survival
        self.max_structures = max_structures
        self.nsteadystate = nsteadystate
        self.nfirst_generation = nfirst_generation

        # Initialize the selector
        if selector == "TruncatedSelection":
            from simmate.toolkit.structure_prediction.evolution.selectors import (
                TruncatedSelection,
            )

            selector = TruncatedSelection()
        else:  # BUG
            raise Exception("We only support TruncatedSelection right now")
        self.selector = selector
        logging.info(
            "Parent selection for mutations will use "
            f"{self.selector.__class__.__name__}."
        )

        # Initialize the workflow if a string was given.
        # Otherwise we should already have a workflow class.
        if workflow == "relaxation.vasp.staged":
            from simmate.workflows.relaxation import Relaxation__Vasp__Staged

            self.workflow = Relaxation__Vasp__Staged

            # Point to the structure datatable that we'll pull from
            # BUG: For now, I assume its the results table of the workflow
            self.individuals_datatable = self.workflow.database_table
            self.calculation_datatable = self.workflow.database_table
            # BUG: these need to be merged and moved outside this if statement
        else:
            raise Exception(
                "Only `relaxation.vasp.staged` is supported in early testing"
            )
        logging.info(f"Individuals will be evaulated using '{self.workflow.name_full}'")
        # BUG: I'll need to rewrite this in the future bc I don't really account
        # for other workflows yet. It would make sense that our workflow changes
        # as the search progresses (e.g. we incorporate DeePMD relaxation once ready)

        # Check if there is an existing search and grab it if so. Otherwise, add
        # the search entry to the DB.
        if SearchDatatable.objects.filter(composition=composition.formula).exists():
            self.search_datatable = SearchDatatable.objects.filter(
                composition=composition.formula,
            ).get()
            # TODO: update, add logs, compare... I need to decide what to do here.
            # also, run _check_stop_condition() to avoid unneccessary restart.
        else:
            self.search_datatable = SearchDatatable(
                composition=composition.formula,
                workflows=[
                    self.workflow.name_full
                ],  # as a list bc we can add new ones later
                individuals_datatable_str=self.individuals_datatable.__name__,
                max_structures=max_structures,
                limit_best_survival=limit_best_survival,
            )
            self.search_datatable.save()
        logging.info(
            "To track the progress while this search runs, you can use the following"
            " in a separate python terminal:\n\n"
            "\tfrom simmate.database.workflow_results import EvolutionarySearch\n"
            f"\tsearch = EvolutionarySearch.objects.get(id={self.search_datatable.id})\n\n"
        )

        # Grab the list of singleshot sources that have been ran before
        # and based off of that list, remove repeated sources
        past_singleshot_sources = (
            self.search_datatable.sources.filter(is_singleshot=True)
            .values_list("name", flat=True)
            .all()
        )
        singleshot_sources = [
            source
            for source in singleshot_sources
            if source not in past_singleshot_sources
        ]
        # BUG: what if I want to rerun any of these even though its been ran before?
        # An example would be rerunning substituitions when new structures are available

        # Initialize the single-shot sources
        self.singleshot_sources = []
        for source in singleshot_sources:

            # if we are given a string, we want initialize the class
            # otherwise it should be a class alreadys
            if type(source) == str:
                source = self._init_common_class(source)

            # and add it to our final list
            self.singleshot_sources.append(source)

        # Initialize the steady-state sources, which are given as a list of
        # (proportion, class/class_str, kwargs) for each. As we go through these,
        # we also collect the proportion list for them.
        self.steadystate_source_proportions = []
        self.steadystate_sources = []
        for proportion, source in steadystate_sources:

            # There are certain transformation sources that don't work for single-element
            # structures, so we check for this here and remove them.
            if len(composition.elements) == 1 and source in [
                "from_ase.AtomicPermutation"
            ]:
                logging.warn(
                    f"{source} is not possible with single-element structures."
                    " This is being removed from your steadystate_sources."
                )
                continue  # skips to next source

            # store proportion value
            self.steadystate_source_proportions.append(proportion)

            # if we are given a string, we want initialize the class
            # otherwise it should be a class already
            if type(source) == str:
                source = self._init_common_class(source)
            # and add it to our final list
            self.steadystate_sources.append(source)

        # Make sure the proportions sum to 1, otherwise scale them. We then convert
        # these to steady-state integers (and round to the nearest integer)
        sum_proportions = sum(self.steadystate_source_proportions)
        if sum_proportions != 1:
            logging.warn(
                "fractions for steady-state sources do not add to 1."
                "We have scaled all sources to equal one to fix this."
            )
            self.steadystate_source_proportions = [
                p / sum_proportions for p in self.steadystate_source_proportions
            ]
        # While these are percent values, we want specific counts. We convert to
        # those here.
        self.steadystate_source_counts = [
            int(p * nsteadystate) for p in self.steadystate_source_proportions
        ]

        # Throughout our search, we want to keep track of which workflows we've
        # submitted to prefect for each structure source as well as how long
        # we were holding a steady-state of submissions. We therefore keep
        # a log of Sources in our database -- where even if we've ran this search
        # before, we still want new entries for each.
        self.singleshot_sources_db = []
        for source in self.singleshot_sources:
            source_db = SourceDatatable(
                name=source.__class__.__name__,
                is_steadystate=False,
                is_singleshot=True,
                search=self.search_datatable,
            )
            source_db.save()
            self.singleshot_sources_db.append(source_db)
        self.steadystate_sources_db = []
        for source in self.steadystate_sources:
            source_db = SourceDatatable(
                name=source.__class__.__name__,
                is_steadystate=True,
                is_singleshot=False,
                search=self.search_datatable,
            )
            source_db.save()
            self.steadystate_sources_db.append(source_db)

        # Initialize the fingerprint database
        # For this we need to grab all previously calculated structures of this
        # compositon too pass in too.
        logging.info("Generating fingerprints for past structures...")
        self.fingerprint_validator = PartialCrystalNNFingerprint(
            composition=composition,
            structure_pool=self.search_datatable.individuals,
        )
        # BUG: should we only do structures that were successfully calculated?
        # If not, there's a chance a structure fails because of something like a
        # crashed slurm job, but it's never submitted again...
        # OPTIMIZE: should we only do final structures? Or should I include input
        # structures and even all ionic steps as well...?
        logging.info("Finished setup")

    def start_search(self, sleep_step=60):

        # See if the singleshot sources have been ran yet. For restarted calculations
        # this will likely not be needed (unless a new source was added)
        self._check_singleshot_sources()

        # this loop will go until I hit 'break' below
        while True:

            # TODO: maybe write summary files to csv...? This may be a mute
            # point because I expect we can follow along in the web UI in the future
            # To that end, I can add a "URL" property

            # Check the stop condition
            # If it is True, we can stop the calc.
            if self._check_stop_condition():
                break  # break out of the while loop
            # Otherwise, keep going!

            # update the fingerprint database with all of the completed structures
            self.fingerprint_validator.update_fingerprint_database()

            # Go through the running workflows and see if we need to submit
            # new ones to meet our steadystate target(s)
            self._check_steadystate_workflows()

            # TODO: Go through the triggered actions
            # self._check_triggered_actions()

            # To save our database load, sleep until we run checks again.
            # OPTIMIZE: ask Prefect if their is an equivalent to Dask's gather/wait
            # functions, so we know exactly when a workflow completes
            # https://docs.dask.org/en/stable/futures.html#waiting-on-futures
            logging.info(
                f"Sleeping for {sleep_step} seconds before running checks again."
            )
            time.sleep(sleep_step)
        logging.info("Stopping the search (remaining calcs will be left to finish).")

    def _check_stop_condition(self):

        # first see if we've hit our maximum limit for structures.
        # Note: because we are only looking at the results table, this is really
        # only counting the number of successfully calculated individuals.
        # Nothing is done to stop those that are still running or to count
        # structures that failed to be calculated
        # {f"{self.fitness_field}__isnull"=False} # when I allow other fitness fxns
        if self.search_datatable.individuals_completed.count() > self.max_structures:
            logging.info(
                f"Maximum number of completed calculations hit (n={self.max_structures}."
            )
            return True
        # The 2nd stop condition is based on how long we've have the same
        # "best" individual. If the number of new individuals calculated (without
        # any becoming the new "best") is greater than limit_best_survival, then
        # we can stop the search.

        # grab the best individual for reference
        best = self.search_datatable.best_individual

        # We need this if-statement in case no structures have completed yet.
        if not best:
            return False

        # count the number of new individuals added AFTER the best one. If it is
        # more than limit_best_survival, we stop the search.
        num_new_structures_since_best = self.search_datatable.individuals.filter(
            # check energies to ensure we only count completed calculations
            energy_per_atom__gt=best.energy_per_atom,
            created_at__gte=best.created_at,
        ).count()
        if num_new_structures_since_best > self.limit_best_survival:
            logging.info(
                f"Best individual has not changed after {self.limit_best_survival}"
                " new individuals added."
            )
            return True
        # If we reached this point, then we haven't hit a stop condition yet!
        return False

    def _check_singleshot_sources(self):
        logging.warn("Singleshot sources not implemented yet. Skipping this step.")
