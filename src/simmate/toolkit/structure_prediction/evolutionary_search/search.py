# -*- coding: utf-8 -*-

# This is the highest-level Class at the moment and all other classes work through
# this one.

import numpy

from pymatgen.core.composition import Composition

from pymatdisc.engine.startup import (
    dynamic_init_stopcondition,
    dynamic_init_trigger,
    dynamic_init_creator,
    dynamic_init_mutator,
    dynamic_init_selector,
    dynamic_init_executor,
    dynamic_init_workflow,
)


class Search:
    def __init__(
        self,
        composition,
        #!!! Some of these sources should be removed for compositions with 1 element type
        sources=[
            (0.20, "RandomSymStructure", {}),
            (0.40, "HeredityASE", {}),
            (0.10, "SoftMutationASE", {}),
            (0.10, "MirrorMutationASE", {}),
            (0.05, "LatticeStrainASE", {}),
            (0.05, "RotationalMutationASE", {}),
            (0.05, "AtomicPermutationASE", {}),
            (0.05, "CoordinatePerturbationASE", {}),
        ],
        selector=("TruncatedSelection", {"percentile": 0.2, "ntrunc_min": 5}),
        triggers=[
            ("InitStructures", {"n_initial_structures": 20}),
            (
                "AddStructures",
                {
                    "n_pending_limit": 0,
                    "n_add_structures": 20,
                },
            ),
        ],
        stop_condition=(
            "BasicStopConditions",
            {
                "max_structures": 200,
                "energy_limit": float("-inf"),
                "same_min_structures": 50,
            },
        ),
        workflow="prefect_workflow",  #!!! TO-DO
        executor=(
            "DaskExecutor",
            {"address": "tcp://152.2.175.15:8786"},
        ),  #!!! Change this to a LocalExecutor for main release
    ):

        # Make sure the composition is a pymatgen object - if not, convert it
        # and then save the composition.
        if isinstance(composition, Composition):
            self.composition = composition
        else:
            self.composition = Composition(composition)

        # data
        #!!! ADD A STEP HERE TO LOAD FROM EXTERNAL DB
        #!!! Consider making each sample (row) and object...?
        self.origins = []
        self.parent_ids = []
        self.structures = []
        self.workflow_futures = []
        self.fitnesses = []
        self.njobs_completed = 0  # This can be inferred from the data above but its computationally cheaper to have this running value

        ### Now initialize all the higher order objects ###

        # Initialize the Sources
        self.source_probabilities = []
        self.sources = []
        for prob, creator_class, creator_kwargs in sources:

            self.source_probabilities.append(prob)

            # dynamically load the creator/transformation source
            try:
                cs_object = dynamic_init_creator(
                    creator_class, creator_kwargs, self.composition
                )
            except AttributeError:
                cs_object = dynamic_init_mutator(
                    creator_class, creator_kwargs, self.composition
                )
            self.sources.append(cs_object)
        # Make sure the probabilites sum to 1, otherwise scale them.
        sum_prob = sum(self.source_probabilities)
        if sum_prob != 1:
            self.source_probabilities = [
                p / sum_prob for p in self.source_probabilities
            ]

        # Initialize Selector
        #!!! I only support one selector for right now. I should allow one for each source
        self.selector = dynamic_init_selector(selector[0], selector[1])

        # Initialize Triggers
        self.triggers = []
        for trigger_class, trigger_kwargs in triggers:
            trigger_object = dynamic_init_trigger(
                trigger_class, trigger_kwargs, self.composition
            )
            self.triggers.append(trigger_object)

        # Initialize Stop Condition
        self.stop_condition = dynamic_init_stopcondition(
            stop_condition[0], stop_condition[1], self.composition
        )

        # Initialize Executor
        self.executor = dynamic_init_executor(executor[0], executor[1])

        # Load Workflow fxn #!!! make into classes in the future...?
        self.workflow = dynamic_init_workflow(workflow)

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
