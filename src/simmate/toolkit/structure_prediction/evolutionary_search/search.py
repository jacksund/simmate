# -*- coding: utf-8 -*-

import numpy

from simmate.configuration.django import setup_full  # sets database connection
from simmate.database.local_calculations.structure_prediction.evolutionary_algorithm import (
    EvolutionarySearch as SearchDatatable,
    # StructureSource as SourceDatatable,
    # Individual as IndividualDatatable,
)

import simmate.toolkit.creators.structure.all as creation_module
import simmate.toolkit.transformations.all as transform_module


class Search:
    def __init__(
        self,
        composition,  # TODO: chemical system? 1,2,3D?
        workflow="MITRelaxation",
        individuals_datatable="MITIndividuals",
        fitness_function="energy",
        # Instead of specifying a stop_condition class like I did before,
        # I just assume the stop condition is either (1) the maximum allowed
        # calculated structures or (2) how long a given structure has been
        # the "best" one.
        max_structures=3000,
        limit_best_survival=250,
        singleshot_sources=[
            "prototypes_aflow",
            "substitution",
            "third_party_structures",
            "third_party_substitution",
        ],
        #!!! Some of these sources should be removed for compositions with 1 element type
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
        # triggered_actions=[],  # TODO: this can be things like "start_ml_potential"
        # executor= # TODO: I assume Prefect for submitting workflows right now.
    ):

        self.composition = composition
        self.limit_best_survival = limit_best_survival
        self.max_structures = max_structures
        self.nsteadystate = nsteadystate

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

        # Initialize the workflow if a string was given.
        # Otherwise we should already have a workflow class.
        if workflow == "MITRelaxation":
            from simmate.workflows.relaxation.mit import workflow
        self.workflow = workflow

        # Load the Individuals datatable class.
        if individuals_datatable == "MITIndividuals":
            from simmate.database.local_calculations.structure_prediction.evolutionary_algorithm import (
                MITIndividuals as individuals_datatable,
            )
        self.individuals_datatable = individuals_datatable

        # Check if there is an existing search and grab it if so. Otherwise, add
        # the search entry to the DB.
        if SearchDatatable.objects.filter(composition=composition.formula).exists():
            self.search_db = SearchDatatable.objects.filter(
                composition=composition.formula,
            ).get()
            # TODO: update, add logs, compare... I need to decide what to do here.
        else:
            self.search_db = SearchDatatable(
                composition=composition.formula,
                workflow=workflow.name,
                individuals_datatable=individuals_datatable.__name__,
                max_structures=max_structures,
                limit_best_survival=limit_best_survival,
            )
            self.search_db.save()

    def run(self):

        while True:  # this loop will go until I hit 'break' below

            # Go through the existing analyses and update them.
            self.check_workflows()

            # save progress to external database #!!! consider moving into a Trigger
            self.save_progress()

            # Check the stop condition
            # If it is True, we can stop the calc.
            if self.stop_condition.check(self):
                break  # break out of the while loop
            # Otherwise, keep going!

            # Using the new data, update my generator #!!! consider moving into a Trigger
            # self.update_sources() #!!! Not implemented yet

            # Go through the triggers
            # I pass self in as an arg because the triggers need the search arg
            self.run_checks_and_actions()

    def _check_stop_condition(self):

        # first see if we've hit our maximum limit for structures.
        # Note: because we are only looking at the results table, this is really
        # only counting the number of successfully calculated individuals.
        # Nothing is done to stop those that are still running or to count
        # structures that failed to be calculated
        if self.individuals_datatable.objects.count() > self.max_structures:
            return True

        # The 2nd stop condition is based on how long we've have the same
        # "best" individual. If the number of new individuals calculated (without
        # any becoming the new "best") is greater than limit_best_survival, then
        # we can stop the search.

        # grab the best individual for reference
        best = (
            self.individuals_datatable.objects.filter(
                structure__formula=self.compositon.formula
            )
            .order_by("structure__energy_per_atom")
            .include("structure")
            .first()
        )

        # count the number of new individuals added AFTER the best one. If it is
        # more than limit_best_survival, we stop the search.
        num_new_indivduals_since_best = self.individuals_datatable.objects.filter(
            structure__formula__gte=self.compositon.formula,
            # check energies to ensure we only count completed calculations
            structure__energy_per_atom__gt=best.structure.energy_per_atom,
            created_at__gte=best.created_at,
        ).count()
        if num_new_indivduals_since_best > self.limit_best_survival:
            return True

        # If we reached this point, then we haven't hit a stop condition yet!
        return False

    def _get_best_individual(self):
        pass

    def save_progress(self):
        #!!! make this into a separate class so I can allow for csv vs sql!
        #!!! This is very inefficient because I rewrite everything instead of just what's new.

        # Go through futures and convert them to keys
        # For executors like Dask, an actual future object can't be stored
        # so I mark any non-string (other than None-type) as unsafe to store
        #!!! change this in the future
        futures = [
            future if not future or type(future) == str else future.key
            for future in self.workflow_futures
        ]

        # save simple data to a csv
        import pandas

        df = pandas.DataFrame.from_dict(
            {
                "workflow_futures": futures,
                "fitness": self.fitnesses,
                "source": self.origins,
                "parent_ids": self.parent_ids,
            }
        )
        df.to_csv("search_backup.csv")

        # save structures as cif files in a folder names 'structures'
        import os

        if not os.path.exists("structures"):
            os.mkdir("structures")
        os.chdir("structures")
        for i, structure in enumerate(self.structures):
            structure.to(
                "poscar", "{}.vasp".format(i)
            )  # I use POSCAR format, which can be opened in VESTA with the .vasp ending
        os.chdir("..")

    def submit_new_sample_workflow(self, structure):  #!!! change to args and kwargs?
        future = self.executor.submit(func=self.workflow, args=[structure], kwargs={})

        self.workflow_futures.append(future)  # future is either Dask Future or key
        self.fitnesses.append(None)  # empty that will be updated later

    def check_workflows(self):

        # I want to keep track of the number of jobs pending
        # This is useful for many Triggers and rather than each trigger
        # running a self.check_njobs_pending() function, its faster/cheaper
        # to update this variable within this looping function
        njobs_pending = 0
        # The same goes for the number of jobs successfully completed.
        # I init this variable above and update it here.

        for sample_id, future in enumerate(self.workflow_futures):
            # for speed I deleted the finished futures and replace them with None
            # This way I'm not constantly making queries for workflows that no
            # longer exist after completion (like in FireWorks executor)
            if future:
                status = self.executor.check(future)
                if status == "done":
                    #!!! THIS IS A STRICT DEFINITON OF WORKFLOW OUTPUT
                    #!!! CHANGE THIS WHEN I CREATE A WORKFLOW CLASS
                    result = self.executor.get_result(future)
                    # update the fitness value
                    self.fitnesses[sample_id] = result["final_energy"]
                    # update the structure
                    self.structures[sample_id] = result["final_structure"]
                    # update the future to None
                    self.workflow_futures[sample_id] = None
                    # update the count of successful calcs
                    self.njobs_completed += 1
                elif status == "error":
                    # This line will raise the error: self.executor.get_result(future)
                    # we don't update the fitness - we just leave it at None
                    # update the future to None so it is no longer checked
                    self.workflow_futures[sample_id] = None
                elif status == "pending":
                    njobs_pending += 1
                    pass  # move on until the job is done!

        # update the number of jobs pendings value
        self.njobs_pending = njobs_pending

    def run_checks_and_actions(self):
        # Go through the triggers
        for trigger in self.triggers:
            if trigger.check(self):
                trigger.action(self)

    def select_parents(self, nselect):
        parents_i = self.selector.select(self.fitnesses, nselect)
        parents = [
            self.structures[i] for i in parents_i
        ]  # grab the corresponding structures
        return parents_i, parents

    def new_sample(self, creators_only=False, max_attempts0=10, max_attempts1=100):

        new_structure = False
        attempt0 = 0
        while not new_structure and attempt0 <= max_attempts0:
            attempt0 += 1
            if creators_only:
                # randomly select the source until we get a creator
                source = None  # to start the loop
                while "creator" not in str(type(source)):
                    source = numpy.random.choice(
                        self.sources, p=self.source_probabilities
                    )
            else:
                # randomly select the source
                source = numpy.random.choice(self.sources, p=self.source_probabilities)

            try:
                print("Attempting with... " + source.__class__.__name__)
            except:
                print("Attempting with... " + str(type(source)))

            # iterate until I get a good structure or run out of attempts
            attempt1 = 0
            while not new_structure and attempt1 <= max_attempts1:
                # add an attempt
                attempt1 += 1
                if "transformation" in str(
                    type(source)
                ):  #!!! NEED MORE EFFICIENT METHOD
                    # grab parent structures using the selection method
                    parents_i, parents = self.select_parents(source.ninput)
                    #!!! This fixes a bug when there's only one structure input (should be Structure, not List)
                    if source.ninput == 1:
                        parents = parents[0]
                    # make a new structure
                    new_structure = source.apply_transformation(parents)
                elif "creator" in str(type(source)):  #!!! NEED MORE EFFICIENT METHOD
                    parents_i = None
                    # make a new structure
                    new_structure = source.create_structure()
            # see if we got a structure or if we hit the max attempts
            if not new_structure:
                print("Failed to create a structure with {}".format(source))
        # see if we got a structure or if we hit the max attempts
        if not new_structure:
            print("Failed to create a structure! Consider changing your settings.")
            return False

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
