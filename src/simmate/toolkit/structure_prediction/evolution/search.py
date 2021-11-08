# -*- coding: utf-8 -*-

import time

from simmate.configuration.django import setup_full  # sets database connection
from simmate.database.local_calculations.structure_prediction.evolution import (
    EvolutionarySearch as SearchDatatable,
    StructureSource as SourceDatatable,
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
        structure_datatable="MITStructure",
        workflow="MITRelaxation",
        # fitness_field="energy_per_atom",  # TODO: I assume this for now.
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
            # "SomeOtherDatatable",  # e.g. taking the best from table of lower quality calculations
        ],
        # No mutations/transforms are done until this many calcs complete
        # this includes those from singleshot and steadystate creators.
        nfirst_generation=40,
        # this is total number of submitted calcs at any given time
        nsteadystate=40,
        # !!! Some of these sources should be removed for compositions with 1 element type
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
        selector="TruncatedSelection",
        # TODO: this can be things like "start_ml_potential" or "update volume in sources"
        # triggered_actions=[],
        # TODO: I assume Prefect for submitting workflows right now.
        # executor="local",
    ):

        self.composition = composition

        # TODO: consider grabbing these from the database so that we can update
        # them at any point.
        self.limit_best_survival = limit_best_survival
        self.max_structures = max_structures
        self.nsteadystate = nsteadystate
        self.nfirst_generation = nfirst_generation

        # Initialize the selector
        if selector == "TruncatedSelection":
            from simmate.toolkit.structure_prediction.evolution.selectors.all import (
                TruncatedSelection,
            )

            selector = TruncatedSelection()
        else:  # BUG
            raise Exception("We only support TruncatedSelection right now. Sorry!")
        self.selector = selector
            
        # Load the Individuals datatable class.
        if structure_datatable == "MITStructure":
            from simmate.database.local_calculations.energy.mit import (
                MITStructure as structure_datatable,
            )
        else:  # BUG
            raise Exception("I only support MITStructure right now")
        self.structure_datatable = structure_datatable

        # Initialize the workflow if a string was given.
        # Otherwise we should already have a workflow class.
        if workflow == "MITRelaxation":
            from simmate.workflows.relaxation.mit import workflow

            self.workflow = workflow
        else:
            raise Exception("Only MITRelaxation is supported in early testing. -Jack")
        # BUG: I'll need to rewrite this in the future bc I don't really account
        # for other workflows yet. It would make sense that our workflow changes
        # as the search progresses (e.g. we incorporate DeePMD relaxation once ready)

        # Check if there is an existing search and grab it if so. Otherwise, add
        # the search entry to the DB.
        if SearchDatatable.objects.filter(composition=composition.formula).exists():
            self.search_db = SearchDatatable.objects.filter(
                composition=composition.formula,
            ).get()
            # TODO: update, add logs, compare... I need to decide what to do here.
            # also, run _check_stop_condition() to avoid unneccessary restart.
        else:
            self.search_db = SearchDatatable(
                composition=composition.formula,
                workflows=[
                    self.workflow.name
                ],  # as a list bc we can add new ones later
                individuals_datatable=structure_datatable.__name__,
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
        # Make sure the proportions sum to 1, otherwise scale them. We then convert
        # these to steady-state integers (and round to the nearest integer)
        sum_proportions = sum(self.steadystate_source_proportions)
        if sum_proportions != 1:
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
            if self._check_stop_condition():
                break  # break out of the while loop
            # Otherwise, keep going!

            # Go through the running workflows and see if we need to submit
            # new ones to meet our steadystate target(s)
            print("A")
            self._check_steadystate_workflows()
            print("DONE")

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
            self.structure_datatable.objects.filter(
                formula_full=self.composition.formula
            )
            .order_by("energy_per_atom")
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
            self.structure_datatable.objects.filter(
                formula_full=self.composition.formula,
                energy_per_atom__isnull=False,
                # **{f"{self.fitness_field}__isnull"=False} # when I allow other fitness fxns
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
        num_new_structures_since_best = self.structure_datatable.objects.filter(
            formula_full=self.composition.formula,
            # check energies to ensure we only count completed calculations
            energy_per_atom__gt=best.energy_per_atom,
            created_at__gte=best.created_at,
        ).count()
        if num_new_structures_since_best > self.limit_best_survival:
            print(
                f"Best individual has not changed after {self.limit_best_survival}"
                " new individuals added."
            )
            return True
        # If we reached this point, then we haven't hit a stop condition yet!
        return False

    def _check_singleshot_sources(self):
        print("Singleshot sources not implemented yet.")

    def _check_steadystate_workflows(self):

        # we iterate through each steady-state source and check to see how many
        # jobs are still running for it. If it's less than the target steady-state,
        # then we need to submit more!
        for source, source_db, njobs_target in zip(
            self.steadystate_sources,
            self.steadystate_sources_db,
            self.steadystate_source_counts,
        ):
            print("C")
            # This loop says for the number of steady state runs we are short,
            # create that many new individuals! max(x,0) ensure we don't get a
            # negative value. A value of 0 means we are at steady-state and can
            # just skip this loop.
            for n in range(max(int(njobs_target - source_db.nprefect_flow_runs), 0)):
                print("D")
                
                # now we need to make a new individual and submit it!
                parent_ids, structure = self._make_new_structure(source)

                # sometimes we fail to make a structure with the source. In cases
                # like this, we warn the user, but just move on. This means
                # we will be short of our steady-state target. The warning for
                # this is done inside _make_new_structure
                if not structure:
                    break
                # submit the structure workflow
                flow_run_id, calc = self.workflow.run_cloud(
                    structure=structure,
                    wait_for_run=False,
                )
                
                # Attached the flow_run_id to our source so we know how many
                # associated jobs are running.
                source_db.prefect_flow_run_ids.append(flow_run_id)
                source_db.save()
                
                # update the source on the calculation
                calc.source = f"{source.__class__.__name__}"
                calc.source_id = parent_ids
                calc.save()

    def _make_new_structure(self, source, max_attempts=100):

        # TODO: check to make sure this structure is unique and hasn't been
        # submitted already. I may have two nested while loops -- one for
        # max_unique_attempts and one for max_creation_attempts.

        # check if we have a transformation or a creator
        # OPTIMIZE: is there a faster way? check subclass maybe?
        if "transformation" in str(type(source)):
            is_transformation = True
        elif "creator" in str(type(source)):
            is_transformation = False
        else:
            raise Exception(
                "Make sure your steady-state sources are either creators or transformations!"
                f" {source.__class__.__name__} does not meet this requirement."
            )

        # transformations require that we have completed structures in the
        # database. We want to wait until there's a set amount before
        # we start mutating the best. We check that here.
        if is_transformation and (
            self.structure_datatable.objects.filter(
                energy_per_atom__isnull=False
            ).count()
            < self.nfirst_generation
        ):
            print(
                f"Search isn't ready for transformations yet. Skipping {source.__class__.__name__}"
            )
            return False, False

        # Until we get a new valid structure (or run out of attempts), keep trying
        # with our given source. Assume we don't have a valid structure until
        # proven otherwise
        print(f"Attempting to create a structure with {source.__class__.__name__}")
        new_structure = False
        attempt = 0
        while not new_structure and attempt <= max_attempts:
            print("E")
            # add an attempt
            attempt += 1
            if is_transformation:
                # grab parent structures using the selection method
                parent_ids, parent_structures = self._select_parents(
                    nselect=source.ninput
                )
                # make a new structure
                new_structure = source.apply_transformation(parent_structures)
            elif not is_transformation:  # if it's a creator
                parent_ids = None
                # make a new structure
                new_structure = source.create_structure()
        # see if we got a structure or if we hit the max attempts and there's
        # a serious problem!
        if not new_structure:
            print(
                "Failed to create a structure! Consider changing your settings or"
                " contact our team for help."
            )
            return False, False
        print("Creation Successful.")

        # return the structure and its parents
        return parent_ids, new_structure

    def _select_parents(self, nselect):

        # our selectors just require a dataframe where we specify the fitness
        # column. So we query our individuals database to give this as an input.
        individuals_df = (
            self.structure_datatable.objects.filter(energy_per_atom__isnull=False)
            .order_by("energy_per_atom")[:200]
            .to_dataframe()
        )
        # NOTE: I assume we'll never need more than the best 200 structures, which
        # may not be true in special cases.

        # From these individuals, select our parent structures
        parents_df = self.selector(nselect, individuals_df, "energy_per_atom")

        # grab the id column of the parents and convert it to a list
        parent_ids = parents_df.id.values.tolist()

        # now lets grab these structures from our database and convert them
        # to a list of pymatgen structures
        parent_structures = (
            self.structure_datatable.objects.filter(id__in=parent_ids)
            .only("structure_string")
            .to_pymatgen()
        )

        # When there's only one structure selected we return the structure and
        # id independents -- not within a list
        if nselect == 1:
            parent_ids = parent_ids[0]
            parent_structures = parent_structures[0]
        # for record keeping, we also want to return the ids for each structure
        return parent_ids, parent_structures

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
