# -*- coding: utf-8 -*-

import time

from prefect import Client

from simmate.configuration.django import setup_full  # sets database connection
from simmate.database.local_calculations.structure_prediction.evolutionary_algorithm import (
    EvolutionarySearch as SearchDatatable,
    StructureSource as SourceDatatable,
    # Individual as IndividualDatatable,
)

import simmate.toolkit.creators.structure.all as creation_module
import simmate.toolkit.transformations.all as transform_module


class Search:
    def __init__(
        self,
        composition,  # TODO: chemical system? 1,2,3D?
        # TODO: what if the workflow changes (e.g. starts with ML relax) but the
        # final table stays the same?
        # workflow="MITRelaxation",  # linked to the individuals_datatable
        individuals_datatable="MITIndividual",
        fitness_function="energy",
        # Instead of specifying a stop_condition class like I did before,
        # I just assume the stop condition is either (1) the maximum allowed
        # calculated structures or (2) how long a given structure has been
        # the "best" one.
        max_structures=3000,
        limit_best_survival=250,
        singleshot_sources=[
            # "prototypes_aflow",
            # "substitution",
            # "third_party_structures",
            # "third_party_substitution",
            # "SomeOtherDatatable",  # this could be useful for pulling from a
            # table of lower quality calculations
        ],
        # !!! Some of these sources should be removed for compositions with 1 element type
        nsteadystate=40,
        steadystate_sources=[
            (0.20, "PyXtalStructure"),
            (0.40, "HeredityASE"),
            (0.10, "SoftMutationASE"),
            (0.10, "MirrorMutationASE"),
            (0.05, "LatticeStrainASE"),
            (0.05, "RotationalMutationASE"),
            (0.05, "AtomicPermutationASE"),
            (0.05, "CoordinatePerturbationASE"),
        ],
        selector=("TruncatedSelection", {"percentile": 0.2, "ntrunc_min": 5}),
        # triggered_actions=[],  # TODO: this can be things like "start_ml_potential" or "update volume in sources"
        # executor= # TODO: I assume Prefect for submitting workflows right now.
    ):

        self.composition = composition

        # TODO: consider grabbing these from the database so that we can update
        # them at any point.
        self.limit_best_survival = limit_best_survival
        self.max_structures = max_structures
        self.nsteadystate = nsteadystate

        # Prefect is required for this class, so we connect to the client upfront
        self.prefect_client = Client()

        # Load the Individuals datatable class.
        if individuals_datatable == "MITIndividual":
            from simmate.database.local_calculations.structure_prediction.evolutionary_algorithm import (
                MITIndividual as individuals_datatable,
            )
        self.individuals_datatable = individuals_datatable

        # Initialize the workflow if a string was given.
        # Otherwise we should already have a workflow class.
        if self.individuals_datatable.workflow == "MITRelaxation":
            from simmate.workflows.relaxation.mit import workflow

            self.workflow = workflow
        else:
            raise Exception("Only MITRelaxation is supported in early testing. -Jack")
        # BUG: I'll need to rewrite this in the future bc I don't really account
        # for other workflows yet

        # Check if there is an existing search and grab it if so. Otherwise, add
        # the search entry to the DB.
        if SearchDatatable.objects.filter(composition=composition.formula).exists():
            self.search_db = SearchDatatable.objects.filter(
                composition=composition.formula,
            ).get()
            # TODO: update, add logs, compare... I need to decide what to do here.
            # also, run _check_stop_condition() to avoid unneccessary restart
        else:
            self.search_db = SearchDatatable(
                composition=composition.formula,
                workflow=workflow.name,
                individuals_datatable=individuals_datatable.__name__,
                max_structures=max_structures,
                limit_best_survival=limit_best_survival,
            )
            self.search_db.save()
        # Grab the list of singleshot sources that have been ran before
        # and based off of that list, remove repeated sources
        past_singleshot_sources = (
            self.search_db.sources.filter(is_singleshot=True)
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

            # store proportion value
            self.steadystate_source_proportions.append(proportion)

            # if we are given a string, we want initialize the class
            # otherwise it should be a class already
            if type(source) == str:
                source = self._init_common_class(source)
            # and add it to our final list
            self.steadystate_sources.append(source)
        # Make sure the proportions sum to 1, otherwise scale them.
        sum_proportions = sum(self.steadystate_source_proportions)
        if sum_proportions != 1:
            self.steadystate_source_proportions = [
                p / sum_proportions for p in self.steadystate_source_proportions
            ]
        # TODO: change to specific values using nsteadystate

        # Throughout our search, we want to keep track of which workflows we've
        # submitted to prefect for each structure source as well as how long
        # we were holding a steady-state of submissions. We therefore keep
        # a log of Sources in our database -- where even if we've ran this search
        # before, we still.
        self.singleshot_sources_db = []
        for source in self.singleshot_sources:
            source_db = SourceDatatable(
                name=source.__class__.__name__,
                is_steadystate=False,
                is_singleshot=True,
                search=self.search_db,
            )
            source_db.save()
            self.singleshot_sources_db.append(source_db)
        self.steadystate_sources_db = []
        for source in self.steadystate_sources:
            source_db = SourceDatatable(
                name=source.__class__.__name__,
                is_steadystate=True,
                is_singleshot=False,
                search=self.search_db,
            )
            source_db.save()
            self.steadystate_sources_db.append(source_db)

    def run(self, sleep_step=10):

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
            if self._check_stop_condition(self):
                break  # break out of the while loop
            # Otherwise, keep going!

            # Go through the running workflows and see if we need to submit
            # new ones to meet our steadystate target(s)
            self._check_steadystate_workflows()

            # TODO: Go through the triggered actions
            # self._check_triggered_actions()

            # To save our database load, sleep until we run checks again.
            # OPTIMIZE: ask Prefect if their is an equivalent to Dask's gather/wait
            # functions, so we know exactly when a workflow completes
            # https://docs.dask.org/en/stable/futures.html#waiting-on-futures
            time.sleep(sleep_step)
        print("Stopping the search (remaining calcs will be left to finish).")

    def get_best_individual(self):
        best = (
            self.individuals_datatable.objects.filter(
                structure__formula_full=self.composition.formula
            )
            .order_by("structure__energy_per_atom")
            .select_related("structure")
            .first()
        )
        return best

    def _check_stop_condition(self):

        # first see if we've hit our maximum limit for structures.
        # Note: because we are only looking at the results table, this is really
        # only counting the number of successfully calculated individuals.
        # Nothing is done to stop those that are still running or to count
        # structures that failed to be calculated
        if (
            self.individuals_datatable.objects.filter(
                structure__formula_full=self.composition.formula,
                structure__energy_per_atom__isnull=False,
            ).count()
            > self.max_structures
        ):
            print(
                f"Maximum number of completed calculations hit (n={self.max_structures}."
            )
            return True
        # The 2nd stop condition is based on how long we've have the same
        # "best" individual. If the number of new individuals calculated (without
        # any becoming the new "best") is greater than limit_best_survival, then
        # we can stop the search.

        # grab the best individual for reference
        best = self.get_best_individual()

        # We need this if-statement in case no structures have completed yet.
        if not best:
            return False
        # count the number of new individuals added AFTER the best one. If it is
        # more than limit_best_survival, we stop the search.
        num_new_indivduals_since_best = self.individuals_datatable.objects.filter(
            structure__formula_full=self.composition.formula,
            # check energies to ensure we only count completed calculations
            structure__energy_per_atom__gt=best.structure.energy_per_atom,
            created_at__gte=best.created_at,
        ).count()
        if num_new_indivduals_since_best > self.limit_best_survival:
            print(
                f"Best individual has not changed after {self.limit_best_survival}"
                " new individuals added."
            )
            return True
        # If we reached this point, then we haven't hit a stop condition yet!
        return False

    def _check_steadystate_workflows(self):

        # we iterate through each steady-state source and check to see how many
        # jobs are still running for it. If it's less than the target steady-state,
        # then we need to submit more!
        for source, source_db, njobs_target in zip(
            self.steadystate_sources,
            self.steadystate_sources_db,
            self.steadystate_source_proportions,
        ):
            if source_db.nprefect_flow_runs < njobs_target:

                # now we need to make a new individual and submit it!
                pass

    def _make_new_individual(self, source, max_attempts=100):

        # TODO: check to make sure this structure is unique and hasn't been
        # submitted already. I may have two nested while loops -- one for
        # max_unique_attempts and one for max_creation_attempts.

        # Until we get a new valid structure (or run out of attempts), keep trying
        # with our given source. Assume we don't have a valid structure until
        # proven otherwise
        print(f"Attempting to create a structure with {source.__class__.__name__}")
        new_structure = False
        attempt = 0
        while not new_structure and attempt <= max_attempts:
            # add an attempt
            attempt += 1
            if "transformation" in str(
                type(source)
            ):  # OPTIMIZE: quick way to check for Transformation subclass?
                # grab parent structures using the selection method
                parents_i, parents = self.select_parents(source.ninput)
                #!!! This fixes a bug when there's only one structure input (should be Structure, not List)
                if source.ninput == 1:
                    parents = parents[0]
                # make a new structure
                new_structure = source.apply_transformation(parents)
            elif "creator" in str(
                type(source)
            ):  # OPTIMIZE: quick way to check for Creator subclass?
                parents_i = None
                # make a new structure
                new_structure = source.create_structure()
        # see if we got a structure or if we hit the max attempts and there's 
        # a serious problem!
        if not new_structure:
            print(
                "Failed to create a structure! Consider changing your settings or"
                " contact our team for help."
            )
            return False
        
        # now let's add this structure to our database
        
        
        
        
        
        # add the new structure to the db list
        self.structures.append(new_structure)
        # add the origin to the db list
        try:
            source_name = source.__class__.__name__
        except:
            source_name = str(type(source))
        self.origins.append(
            source_name
        )  #!!! I should add a source.name feature #!!! what if two sources share a parent class?
        self.parent_ids.append(parents_i)

        # add the workflow for the structure
        # let the analysis object handle adding things to the database
        self.submit_new_sample_workflow(new_structure)

        print("Creation Successful and Structure Submitted")

        # return True to indicate success
        return True

    def _init_common_class(self, class_str):

        # CREATORS
        if class_str in [
            "RandomSymStructure",
            "PyXtalStructure",
        ]:
            mutation_class = getattr(creation_module, class_str)
            return mutation_class(self.composition)
        # TRANSFORMATIONS
        elif class_str in [
            "HeredityASE",
            "SoftMutationASE",
            "MirrorMutationASE",
            "LatticeStrainASE",
            "RotationalMutationASE",
            "AtomicPermutationASE",
            "CoordinatePerturbationASE",
        ]:
            mutation_class = getattr(transform_module, class_str)
            return mutation_class(self.composition)
        # !!! There aren't any common transformations that don't accept composition
        # as an input, but I expect this to change in the future.
        elif class_str in []:
            mutation_class = getattr(transform_module, class_str)
            return mutation_class()
        # These are commonly used Single-shot sources
        elif class_str == "prototypes_aflow":
            pass  # TODO
        elif class_str == "substitution":
            pass  # TODO
        elif class_str == "third_party_structures":
            pass  # TODO
        elif class_str == "third_party_substitution":
            pass  # TODO
        else:
            raise Exception(
                f"{class_str} is not recognized as a common input. Make sure you"
                "don't have any typos, and if you are using a custom class, provide"
                "your input as an object."
            )
