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
from .individual_from_creator import StructurePrediction__Python__IndividualFromCreator
from .individual_from_transformation import (
    StructurePrediction__Python__IndividualFromTransformation,
)

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
        composition: Union[str, Composition],
        subworkflow_name: Union[str, Workflow] = "relaxation.vasp.staged",
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

        cls._check_stop_condition(search_datatable)

        # See if the singleshot sources have been ran yet. For restarted calculations
        # this will likely not be needed (unless a new source was added). But for
        # new searches/compositions, this will submit all individuals from the
        # single shot sources before we even start the steady-state runs
        cls._check_singleshot_sources(search_datatable, singleshot_sources)

        # Initialize the steady state sources by saving their config information
        # to the database.
        steadystate_sources_db = cls._init_steadystate_sources_to_db(
            composition,
            search_datatable,
            steadystate_sources,
        )

        logging.info("Finished setup")
        logging.info("Assigned this to EvolutionarySearch id={search_datatable.id}.")

        # this loop will go until I hit 'break' below
        while True:

            # TODO: maybe write summary files to csv...? This may be a mute
            # point because I expect we can follow along in the web UI in the future
            # To that end, I can add a "URL" property

            # Check the stop condition
            # If it is True, we can stop the calc.
            if cls._check_stop_condition(search_datatable):
                break  # break out of the while loop
            # Otherwise, keep going!

            # TODO: Go through triggered actions that would update the database
            # table -- e.g. the workflow to run, the validators, etc.
            # self._check_triggered_actions()

            # Go through the running workflows and see if we need to submit
            # new ones to meet our steadystate target(s)
            cls._check_steadystate_workflows(
                search_datatable,
                steadystate_sources_db,
            )

            # To save our database load, sleep until we run checks again.
            logging.info(
                f"Sleeping for {sleep_step} seconds before running checks again."
            )
            time.sleep(sleep_step)

        logging.info("Stopping the search (remaining calcs will be left to finish).")

    @staticmethod
    def _check_stop_condition(search_datatable):

        # first see if we've hit our maximum limit for structures.
        # Note: because we are only looking at the results table, this is really
        # only counting the number of successfully calculated individuals.
        # Nothing is done to stop those that are still running or to count
        # structures that failed to be calculated
        # {f"{self.fitness_field}__isnull"=False} # when I allow other fitness fxns
        if (
            search_datatable.individuals_completed.count()
            > search_datatable.max_structures
        ):
            logging.info(
                "Maximum number of completed calculations hit "
                f"(n={search_datatable.max_structures}."
            )
            return True
        # The 2nd stop condition is based on how long we've have the same
        # "best" individual. If the number of new individuals calculated (without
        # any becoming the new "best") is greater than limit_best_survival, then
        # we can stop the search.

        # grab the best individual for reference
        best = search_datatable.best_individual

        # We need this if-statement in case no structures have completed yet.
        if not best:
            return False

        # count the number of new individuals added AFTER the best one. If it is
        # more than limit_best_survival, we stop the search.
        num_new_structures_since_best = search_datatable.individuals.filter(
            # check energies to ensure we only count completed calculations
            energy_per_atom__gt=best.energy_per_atom,
            created_at__gte=best.created_at,
        ).count()
        if num_new_structures_since_best > search_datatable.limit_best_survival:
            logging.info(
                "Best individual has not changed after "
                f"{search_datatable.limit_best_survival} new individuals added."
            )
            return True
        # If we reached this point, then we haven't hit a stop condition yet!
        return False

    @staticmethod
    def _check_singleshot_sources(search_datatable, singleshot_sources):
        logging.warn("Singleshot sources not implemented yet. Skipping this step.")
        return
        # Initialize the single-shot sources
        # singleshot_sources = []
        # for source in singleshot_sources:
        #     # if we are given a string, we want initialize the class
        #     # otherwise it should be a class alreadys
        #     if type(source) == str:
        #         source = self._init_common_class(source)
        #     # and add it to our final list
        #     self.singleshot_sources.append(source)
        # singleshot_sources_db = []
        # for source in self.singleshot_sources:
        #     source_db = SourceDatatable(
        #         name=source.__class__.__name__,
        #         is_steadystate=False,
        #         is_singleshot=True,
        #         search=self.search_datatable,
        #     )
        #     source_db.save()
        #     self.singleshot_sources_db.append(source_db)

    @staticmethod
    def _init_steadystate_sources_to_db(
        composition,
        search_datatable,
        steadystate_sources,
    ):

        # Initialize the steady-state sources, which are given as a list of
        # (proportion, class/class_str, kwargs) for each. As we go through these,
        # we also collect the proportion list for them.
        steadystate_sources_cleaned = []
        steadystate_source_proportions = []
        for proportion, source_name in steadystate_sources:

            # There are certain transformation sources that don't work for single-element
            # structures, so we check for this here and remove them.
            if len(composition.elements) == 1 and source_name in [
                "from_ase.AtomicPermutation"
            ]:
                logging.warn(
                    f"{source_name} is not possible with single-element structures."
                    " This is being removed from your steadystate_sources."
                )
                steadystate_sources.pop()
                continue  # skips to next source

            # Store proportion value and name of source. We do NOT initialize
            # the source because it will be called elsewhere (within the submitted
            # workflow and therefore a separate thread.
            steadystate_sources_cleaned.append(source_name)
            steadystate_source_proportions.append(proportion)

        # Make sure the proportions sum to 1, otherwise scale them. We then convert
        # these to steady-state integers (and round to the nearest integer)
        sum_proportions = sum(steadystate_source_proportions)
        if sum_proportions != 1:
            logging.warn(
                "fractions for steady-state sources do not add to 1."
                "We have scaled all sources to equal one to fix this."
            )
            steadystate_source_proportions = [
                p / sum_proportions for p in steadystate_source_proportions
            ]
        # While these are percent values, we want specific counts. We convert to
        # those here.
        steadystate_source_counts = [
            int(p * search_datatable.nsteadystate)
            for p in steadystate_source_proportions
        ]

        # Throughout our search, we want to keep track of which workflows we've
        # submitted for each source as well as how long we were holding a
        # steady-state of submissions. We therefore keep a log of Sources in
        # our database.
        steadystate_sources_db = []
        for source_name, ntarget_jobs in zip(
            steadystate_sources_cleaned, steadystate_source_counts
        ):
            # before saving, we want to record whether we have a creator or transformation
            # !!! Is there a way to dynamically determine this from a string?
            # Or maybe initialize them to provide they work before we register?
            # Third option is to specify with the input.
            known_creators = [
                "RandomSymStructure",
                "PyXtalStructure",
            ]
            is_creator = True if source_name in known_creators else False
            known_transformations = [
                "from_ase.Heredity",
                "from_ase.SoftMutation",
                "from_ase.MirrorMutation",
                "from_ase.LatticeStrain",
                "from_ase.RotationalMutation",
                "from_ase.AtomicPermutation",
                "from_ase.CoordinatePerturbation",
            ]
            is_transformation = True if source_name in known_transformations else False
            if not is_creator and not is_transformation:
                raise Exception("Unknown source being used.")
                # BUG: I should really allow any subclass of Creator/Transformation

            source_db = SourceDatatable(
                name=source_name,
                # kwargs --> default for now,
                is_steadystate=True,
                is_singleshot=False,
                is_creator=is_creator,
                is_transformation=is_transformation,
                nsteadystate_target=ntarget_jobs,
                search=search_datatable,
            )
            source_db.save()
            steadystate_sources_db.append(source_db)
        # !!! What if this search has been ran before or a matching search is
        # being ran elsewhere? Do we still want new entries for each?

        return steadystate_sources_db

    @staticmethod
    def _check_steadystate_workflows(search_datatable, steadystate_sources_db):

        # transformations from a database table require that we have
        # completed structures in the database. We want to wait until there's
        # a set amount before we start mutating the best. We check that here.
        if (
            search_datatable.individuals_completed.count()
            < search_datatable.nfirst_generation
        ):
            logging.info(
                "Search hasn't finish 'generation 1' one yet. "
                "Skipping all steady-state sources that are transformations."
            )
            ready_for_transformations = False
        else:
            ready_for_transformations = True

        # we iterate through each steady-state source and check to see how many
        # jobs are still running for it. If it's less than the target steady-state,
        # then we need to submit more!
        for source_db in steadystate_sources_db:

            # skip if we have a transformation but aren't ready for it yet
            if source_db.is_transformation and not ready_for_transformations:
                continue

            # This loop says for the number of steady state runs we are short,
            # create that many new individuals! max(x,0) ensure we don't get a
            # negative value. A value of 0 means we are at steady-state and can
            # just skip this loop.
            for n in range(
                max(int(source_db.nsteadystate_target - source_db.nflow_runs), 0)
            ):

                # submit the workflow for the new individual. Note, the structure
                # won't be evuluated until the job actually starts. This allows
                # our validator to have the most current information available
                # when starting the structure creation

                if source_db.is_transformation:
                    workflow = StructurePrediction__Python__IndividualFromCreator
                    state = workflow.run_cloud()

                elif source_db.is_transformation:
                    workflow = StructurePrediction__Python__IndividualFromTransformation
                    state = workflow.run_cloud()
                else:
                    raise Exception(
                        "A structure source can't be both a creator and a transformation. "
                        "Something is configured incorrectly."
                    )

                # Attached the id to our source so we know how many
                # associated jobs are running.
                # NOTE: this is the WorkItem id and NOT the run_id!!!
                source_db.run_ids.append(state.pk)
                source_db.save()
