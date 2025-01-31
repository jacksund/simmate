# -*- coding: utf-8 -*-

import logging
import math
import traceback
from pathlib import Path

import numpy
import pandas
import plotly.express as plotly_express
import plotly.graph_objects as plotly_go
from django.db.models import F, functions
from django.utils import timezone
from rich.progress import track

from simmate.apps.evolution import selectors as selector_module
from simmate.apps.evolution.models import SteadystateSource
from simmate.configuration.dask import get_dask_client
from simmate.database.base_data_types import Calculation, table_column
from simmate.engine.execution import WorkItem
from simmate.toolkit import Composition, Structure
from simmate.toolkit.validators import fingerprint as validator_module
from simmate.utilities import get_directory
from simmate.visualization.plotting import PlotlyFigure


class FixedCompositionSearch(Calculation):
    """
    This database table holds all of the information related to an evolutionary
    search and also has convient methods to analyze the data + write output files.
    """

    class Meta:
        app_label = "workflows"

    # !!! consider making a composition-based mixin
    composition = table_column.CharField(max_length=50, null=True, blank=True)

    # Import path for the workflow and the database table of results
    subworkflow_name = table_column.CharField(max_length=200, null=True, blank=True)
    subworkflow_kwargs = table_column.JSONField(default=dict, null=True, blank=True)
    fitness_field = table_column.CharField(max_length=200, null=True, blank=True)
    fitness_function = table_column.CharField(max_length=200, null=True, blank=True)
    target_value = table_column.FloatField(
        null=True, blank=True
    )  # Only set if fitness function is target_value

    # Other settings for the search
    min_structures_exact = table_column.IntegerField(null=True, blank=True)
    max_structures = table_column.IntegerField(null=True, blank=True)
    best_survival_cutoff = table_column.IntegerField(null=True, blank=True)
    nfirst_generation = table_column.IntegerField(null=True, blank=True)
    nsteadystate = table_column.IntegerField(null=True, blank=True)
    convergence_cutoff = table_column.FloatField(null=True, blank=True)

    # Key classes to use during the search
    selector_name = table_column.CharField(max_length=200, null=True, blank=True)
    selector_kwargs = table_column.JSONField(default=dict, null=True, blank=True)
    validator_name = table_column.CharField(max_length=200, null=True, blank=True)
    validator_kwargs = table_column.JSONField(default=dict, null=True, blank=True)
    singleshot_sources = table_column.JSONField(default=list, null=True, blank=True)
    # stop_condition_name ---> assumed for now
    # information about the steadystate_sources are stored within
    # the SteadstateSource datatable

    # the time to sleep between file writing and steady-state checks.
    sleep_step = table_column.FloatField(null=True, blank=True)

    # Loading all unique structures is an expensive operation so its only
    # done on a cycle. This stores the list of unique ids.
    unique_individuals_ids = table_column.JSONField(
        default=list,
        null=True,
        blank=True,
    )

    # This is an optional an input for an expected structure in order to allow
    # creation of plots that show convergence vs. the expected. This is very
    # useful benchmarking and when the user has a target structure that they
    # hope to see. For now, this MUST a dictionary input (either pymatgen.as_dict()
    # that points to another table entry because we don't want to use the
    # Structure mix-in on this table (too many unecessary columns)
    expected_structure = table_column.JSONField(default=dict)

    # TODO:
    #   parent_variable_nsite_searches
    #   parent_binary_searches
    #   parent_ternary_searches

    # -------------------------------------------------------------------------
    # Setup of the database tables at the beginning of a new search
    # -------------------------------------------------------------------------

    @classmethod
    def from_toolkit(
        cls,
        steadystate_sources: dict = None,
        as_dict: bool = False,
        **kwargs,
    ):
        # Initialize the steady state sources by saving their config information
        # to the database.
        if steadystate_sources and not as_dict:
            search = cls(**kwargs)
            search.save()  # we must save up front because of relations
            search._init_steadystate_sources_to_db(steadystate_sources)
            return search

        elif not steadystate_sources:
            return kwargs if as_dict else cls(**kwargs)

        if steadystate_sources and as_dict:
            raise Exception(
                "steadystate_sources cannot be set in an as_dict mannor because"
                "it points to a related database table"
            )

    # -------------------------------------------------------------------------
    # Highest-level methods that run the overall search
    # -------------------------------------------------------------------------

    def check_stop_condition(self):
        # First, see if we have at least our minimum limit for *exact* structures.
        # "Exact" refers to the nsites of the structures. We want to ensure at
        # least N structures with the input/expected number of sites have been
        # calculated.
        count_exact = self.individuals_datatable.objects.filter(
            formula_full=self.composition,
            workflow_name=self.subworkflow_name,
            **{f"{self.fitness_field}__isnull": False},
        ).count()
        if count_exact < self.min_structures_exact:
            return False

        # Next, see if we've hit our maximum limit for structures.
        # Note: because we are only looking at the results table, this is really
        # only counting the number of successfully calculated individuals.
        # Nothing is done to stop those that are still running or to count
        # structures that failed to be calculated
        # {f"{self.fitness_field}__isnull"=False} # when I allow other fitness fxns
        if self.individuals_completed.count() > self.max_structures:
            logging.info(
                "Maximum number of completed calculations hit "
                f"(n={self.max_structures})."
            )
            return True

        # The next stop condition is based on how long we've have the same
        # "best" individual. If the number of new individuals calculated (without
        # any becoming the new "best") is greater than best_survival_cutoff, then
        # we can stop the search.
        # grab the best individual for reference
        best = self.best_individual

        # We need this if-statement in case no structures have completed yet.
        if not best:
            return False

        # count the number of new individuals added AFTER the best one. If it is
        # more than best_survival_cutoff, we stop the search.
        # Note, we look at all structures that have an energy_per_atom greater
        # than 1meV/atom higher than the best structure. The +1meV ensures
        # we aren't prolonging the calculation for insignificant changes in
        # the best structure. Looking at the energy also ensures that we are
        # only counting completed calculations.
        # BUG: this filter needs to be updated to fitness_value and not
        # assume we are using energy_per_atom
        best_value = getattr(best, self.fitness_field)
        if self.fitness_function == "min":
            num_new_structures_since_best = self.individuals.filter(
                finished_at__gte=best.finished_at,
                **{f"{self.fitness_field}__gt": best_value + self.convergence_cutoff},
            ).count()

        elif self.fitness_function == "max":
            num_new_structures_since_best = self.individuals.filter(
                finished_at__gte=best.finished_at,
                **{f"{self.fitness_field}__gt": best_value - self.convergence_cutoff},
            ).count()

        elif self.fitness_funtion == "target_value":
            pass  # TODO

        if num_new_structures_since_best > self.best_survival_cutoff:
            logging.info(
                "Best individual has not changed after "
                f"{self.best_survival_cutoff} new individuals added."
            )
            return True
        # If we reached this point, then we haven't hit a stop condition yet!
        return False

    def _check_singleshot_sources(self, directory: Path):
        # local imports to prevent circuluar import issues
        from simmate.apps.evolution.singleshot_sources.known import get_known_structures
        from simmate.apps.evolution.singleshot_sources.prototypes import (
            get_structures_from_prototypes,
        )
        from simmate.apps.evolution.singleshot_sources.substitution import (
            get_structures_from_substitution_of_known,
        )
        from simmate.apps.evolution.workflows.utilities import (
            write_and_submit_structures,
        )

        composition = Composition(self.composition)

        if "third_parties" in self.singleshot_sources:
            structures_known = get_known_structures(
                composition,
                allow_multiples=False,
                remove_matching=True,
            )
            logging.info(
                f"Generated {len(structures_known)} structures from third-party databases"
            )
            write_and_submit_structures(
                structures=structures_known,
                foldername=directory / "from_third_parties",
                workflow=self.subworkflow,
                workflow_kwargs=self.subworkflow_kwargs,
            )

        if "third_party_substituition" in self.singleshot_sources:
            structures_sub = get_structures_from_substitution_of_known(
                composition,
                allow_multiples=False,
            )
            logging.info(
                f"Generated {len(structures_sub)} structures from substitutions"
            )
            write_and_submit_structures(
                structures=structures_sub,
                foldername=directory / "from_third_party_substituition",
                workflow=self.subworkflow,
                workflow_kwargs=self.subworkflow_kwargs,
            )

        if "prototypes" in self.singleshot_sources:
            structures_prototype = get_structures_from_prototypes(
                composition,
                max_sites=int(composition.num_atoms),
                remove_matching=True,
            )
            logging.info(
                f"Generated {len(structures_prototype)} structures from prototypes"
            )
            write_and_submit_structures(
                structures=structures_prototype,
                foldername=directory / "from_prototypes",
                workflow=self.subworkflow,
                workflow_kwargs=self.subworkflow_kwargs,
            )

    def _init_steadystate_sources_to_db(self, steadystate_sources):
        composition = Composition(self.composition)

        # Initialize the steady-state sources, which are given as a list of
        # (proportion, class/class_str, kwargs) for each. As we go through
        # these, we also collect the proportion list for them.
        steadystate_sources_cleaned = []
        steadystate_source_proportions = []
        for source_name, proportion in steadystate_sources.items():
            # There are certain transformation sources that don't work for
            # single-element structures, so we check for this here and
            # remove them.
            if len(composition.elements) == 1 and source_name in [
                "from_ase.AtomicPermutation"
            ]:
                logging.warning(
                    f"{source_name} is not possible with single-element structures."
                    " This is being removed from your steadystate_sources."
                )
                continue  # skips to next source

            # There are also transformations that don't work for single-atom
            # structures.
            if composition.num_atoms == 1 and source_name in ["from_ase.Heredity"]:
                logging.warning(
                    f"{source_name} is not possible with single-atom structures."
                    " This is being removed from your steadystate_sources."
                )
                continue  # skips to next source
            # Store proportion value and name of source. We do NOT initialize
            # the source because it will be called elsewhere (within the submitted
            # workflow and therefore a separate thread.
            steadystate_sources_cleaned.append(source_name)
            steadystate_source_proportions.append(proportion)
        # Make sure the proportions sum to 1, otherwise scale them. We then convert
        # these to steady-state integers (and round to the nearest integer)
        sum_proportions = sum(steadystate_source_proportions)
        if not math.isclose(sum_proportions, 1, rel_tol=1e-6):
            logging.warning(
                "fractions for steady-state sources do not add to 1. "
                "We have scaled all sources to equal one to fix this."
            )
            steadystate_source_proportions = [
                p / sum_proportions for p in steadystate_source_proportions
            ]

        # BUG-FIX: Using specific counts could lead to biases towards a given
        # steady-state source if it's generated structures take less time to
        # relax. We revert to proportions.
        # # While these are percent values, we want specific counts. We convert to
        # # those here.
        # steadystate_source_counts = [
        #     int(p * self.nsteadystate) for p in steadystate_source_proportions
        # ]

        # Throughout our search, we want to keep track of which workflows we've
        # submitted for each source as well as how long we were holding a
        # steady-state of submissions. We therefore keep a log of Sources in
        # our database.
        steadystate_sources_db = []
        # for source_name, ntarget_jobs in zip(
        #     steadystate_sources_cleaned, steadystate_source_counts
        # ):
        for source_name, target_proportion in zip(
            steadystate_sources_cleaned, steadystate_source_proportions
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
                "ExtremeSymmetry",
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

            source_db = SteadystateSource(
                name=source_name,
                is_creator=is_creator,
                is_transformation=is_transformation,
                nsteadystate_target=target_proportion,
                search=self,
                target_history=[target_proportion],
                target_time_history=timezone.now(),
                workitem_ids_history=[0],
            )
            source_db.save()
            steadystate_sources_db.append(source_db)
        # !!! What if this search has been ran before or a matching search is
        # being ran elsewhere? Do we still want new entries for each?

        return steadystate_sources_db

    def _check_steadystate_workflows(self):
        # local import to prevent circular import issues
        from simmate.apps.evolution.workflows.new_individual import (
            StructurePrediction__Toolkit__NewIndividual,
        )

        # transformations from a database table require that we have
        # completed structures in the database. We want to wait until there's
        # a set amount before we start mutating the best. We check that here.
        if self.individuals_completed.count() < self.nfirst_generation:
            logging.info(
                "Search hasn't finished nfirst_generation yet "
                f"({self.individuals_completed.count()}/{self.nfirst_generation} individuals). "
                "Skipping transformations."
            )
            ready_for_transformations = False
        else:
            ready_for_transformations = True

        # BUG-FIX: If one steady-state source results in structures that relax
        # much faster than others, and we submit up to a set integer,
        # we will get more than our desired ratio of this steady-state source over
        # the course of the run.
        # Instead, we first check how many structures
        # below our target we are. We then check how many jobs from each source
        # is pending, running, or finished (not failed). Then, for each source we
        # check how far we are from the desired ratio and submit jobs to get to
        # the closest match we can.
        # NOTE: At the beginning of a run, we allow creators to submit up to the
        # target steadystate number. This will still bias the beginning of the
        # calculation towards creators over transformations, but over time it
        # will balance out.
        steadystate_sources_db = self.steadystate_sources.all()
        # Get our target number of runs
        target_nsteadystate = self.nsteadystate
        # prepare objects to store the total number of runs, list of current
        # desired proportions, and list of submitted/finished runs for each source
        active_nsteadystate = 0
        nsteadystate_proportions = []
        nsteadystate_totals = []
        sources_to_add = []
        for source_db in steadystate_sources_db:
            if source_db.is_transformation and not ready_for_transformations:
                continue  # We continue so that we don't consider this source

            # In this loop we want to get the total number of active runs to
            # compare with our target. We also want to get the number of runs
            # that have been submitted for each source (pending, running or finished)

            not_failed = source_db.n_recent_not_failed_workitems
            # NOTE we include all active workitems, even those from before the
            # last source update. This prevents us from submitting a large
            # number of new jobs if there are still some left to run.
            still_active = source_db.n_active_workitems
            active_nsteadystate += still_active
            nsteadystate_proportions.append(source_db.nsteadystate_target)
            nsteadystate_totals.append(not_failed)
            # list corresponds to source database, number to submit
            sources_to_add.append([source_db, 0])

        # We need to normalize our proportions in case we are not ready for
        # transformations.
        nsteadystate_proportions = numpy.array(nsteadystate_proportions)
        nsteadystate_proportions /= nsteadystate_proportions.sum()
        nsteadystate_totals = numpy.array(nsteadystate_totals)
        if nsteadystate_totals.sum() != 0:
            nsteadystate_current_proportions = (
                nsteadystate_totals / nsteadystate_totals.sum()
            )
        else:
            nsteadystate_current_proportions = nsteadystate_totals

        # Now, for each desired new submissions, we want to make a submission
        # such that it adjusts our current proportions as close to the ideal as
        # possible. To do this, we see which proportion is the farthest below
        # ideal and add one submission to it.
        # NOTE: this is easy, but won't always be the addition that improves the
        # proportion the most. Additions to smaller proportions will have a
        # larger effect then greater. However, it should converge over time
        if len(sources_to_add) > 0:
            for i in range(target_nsteadystate - active_nsteadystate):
                # get difference from ideal
                proportion_diff = (
                    nsteadystate_current_proportions - nsteadystate_proportions
                )
                # get the index of the minimum value which represents the source
                # farthest from ideal
                source_idx = numpy.where(proportion_diff == proportion_diff.min())[0][0]
                # adjust our would be steadystate totals and get new proportions
                nsteadystate_totals[source_idx] += 1
                nsteadystate_current_proportions = (
                    nsteadystate_totals / nsteadystate_totals.sum()
                )
                # add one for this source in our sources_to_add dict
                sources_to_add[source_idx][1] += 1

        # We now have the desired number of individuals to add for each source
        # and can add them.
        for source_db, nflows_to_submit in sources_to_add:
            if nflows_to_submit > 0:
                logging.info(
                    f"Submitting {nflows_to_submit} new individuals for "
                    f"'{source_db.name}'"
                )

            # disable the logs while we submit
            logger = logging.getLogger()
            logger.disabled = True

            for n in range(nflows_to_submit):
                # submit the workflow for the new individual. Note, the structure
                # won't be evuluated until the job actually starts. This allows
                # our validator to have the most current information available
                # when starting the structure creation
                state = StructurePrediction__Toolkit__NewIndividual.run_cloud(
                    search_id=self.id,
                    steadystate_source_id=source_db.id,
                    # NOTE: we *only* pass tags because that is all that is
                    # relevent for submission. All other kwargs are passed
                    # within the new-individual workflow to the expected subflow
                    tags=self.subworkflow_kwargs.get("tags", []),
                )

                # Attached the id to our source so we know how many
                # associated jobs are running.
                # NOTE: this is the WorkItem id and NOT the run_id!!!
                source_db.workitem_ids.append(state.pk)
                source_db.save()

            # reactivate logging
            logger.disabled = False

    def _adjust_steadystate_sources(
        self,
        min_generation: float = 5,
        min_proportion: float = 0.01,
    ):
        """
        This function adjusts the target proportions for each steadystate. The
        quality of each steadystate source is ranked based on the energy of new
        structures relative to their parents.The target proportions are then
        increased for structures will a high success rate and decreased for
        others.
        Note that the quality is only checked for jobs finished since the last
        time the proportions were adjusted. This is done in case a source
        starts to be better or worse at different stages of the search.

        Creators such as RandomSymStructure are not included.

        If triggered actions are implemented, this should be moved there.
        """
        # Possible implementations:
        # Use frequency of structure being better than parent
        # Use average of energy difference of structure from parent
        # !!! Once we settle on one, the following code could be much more
        # concise
        # Should sources be allowed to go to zero? I think probably not
        # Steps:
        # 1. Check if its time to update steadystate sources.
        # 2. For each source, pull the finished runs and their parents
        # 3. Calculate energy differences
        # 4. Rank
        # To get the results and parent results we can sort the subworkflow table
        # by time (since the last update for the table) and source. Then we will
        # need to iterate over each row, get the fitness field from the last
        # workflow in the subworkflow, and the fitness field(s) from the source
        # parent id(s).
        # First we check if we have met our condition for when to update steadystate
        # sources. This is done by checking that we have finished a set number
        # of runs since our last update
        steadystate_sources_db = self.steadystate_sources.all()
        # Create metric for if condition is met. We will check that all sources
        # have generated at least the required number of runs
        condition_met = True
        for source_db in steadystate_sources_db:
            if source_db.nsteadystate_target == 0:
                # This source was either removed or is not desired so we skip
                continue
            # We specifically want to check that we have finished enough runs
            # from this source since the last time we updated
            not_failed = source_db.n_recent_not_failed_workitems
            still_active = source_db.n_recent_active_workitems
            finished = not_failed - still_active
            if finished < min_generation:
                condition_met = False
                break
        # if our condition is not met we simply exit
        if not condition_met:
            return
        logging.info("Updating steadystate source proportions")
        # Now we need the results for each source database. Lets set up a dictionary
        transformation_source_results = {}
        transformation_idxs = []
        creator_proportions = 0
        for i, source_db in enumerate(steadystate_sources_db):
            if source_db.is_creator:
                # We don't want to consider creators as these should stay the
                # same to encourage diversity. However, we do want to update
                # them so that our _check_steadystate_workflows method is
                # updating properly
                source_db.update_flow_target(source_db.nsteadystate_target)
                creator_proportions += source_db.nsteadystate_target
                continue
            elif source_db.is_transformation and source_db.nsteadystate_target == 0:
                # This source has been set to 0 and we don't want to consider it
                continue
            transformation_source_results[source_db.name] = {
                "child_results": [],
                "parent_results": [],
            }
            transformation_idxs.append(i)
        # Now we want to go through our results table and pull the energies for
        # each finished individual
        for individual in self.individuals_completed.all():
            if "transformation" in individual.source.keys():
                transformation = individual.source["transformation"]
                # check if parent transformation exists in our transformation
                # source dict. If not, we skip.
                if transformation not in transformation_source_results.keys():
                    continue
                parent_ids = individual.source["parent_ids"]
                if type(parent_ids) == int:
                    # when there is only one parent it is stored as an int
                    # rather than a list
                    parent_ids = [parent_ids]
            else:
                # we have a creator and just want to continue
                continue
            # get the deep subworkflow's results
            child_result = individual.subworkflow_results[-1]
            child_value = getattr(child_result, self.fitness_field)
            for parent_id in parent_ids:
                parent_result = self.individuals_datatable.objects.filter(
                    id=parent_id
                ).first()
                parent_value = getattr(parent_result, self.fitness_field)
                # add child and parent to lists. We add the child for each parent
                transformation_source_results[transformation]["child_results"].append(
                    child_value
                )
                transformation_source_results[transformation]["parent_results"].append(
                    parent_value
                )
        # We now have a dictionary containing the information for each parent
        # and child. Lets get the difference between each to get a metric for
        # how well each source is performing
        source_fitness_averages = []
        source_fitness_stddev = []
        for source_name, results_dict in transformation_source_results.items():
            child_results = numpy.array(results_dict["child_results"])
            parent_results = numpy.array(results_dict["parent_results"])
            # For all fitness functions, we want the best result to have the
            # highest value
            if self.fitness_function == "min":
                # if the child is much better than the parent, this will return
                # a higher value
                improvement = parent_results - child_results
            elif self.fitness_function == "max":
                # In this case we flip the subtractrion so that higher values for
                # children give higher values in the difference
                improvement = child_results - parent_results
            elif self.fitness_function == "target_value":
                # In this case we want to see if we are closer to the target
                # value than the parent.
                parent_dist = numpy.abs(parent_results - self.target_value)
                child_dist = numpy.abs(child_results - self.target_value)
                # We want the value to be higher when the child_dist is smaller
                # than the parent dist so we subtract as follows
                improvement = parent_dist - child_dist
            source_fitness_averages.append(numpy.average(improvement))
            source_fitness_stddev.append(numpy.std(improvement))
        # Now that we have the averages, we want to use them in some way to
        # adjust the steadystate proportions.
        # BUG: There may be a better way to do this
        source_fitness_averages = numpy.array(source_fitness_averages)
        # adjust to worst source
        adjusted_averages = source_fitness_averages - source_fitness_averages.min()
        # normalize to proper range
        new_props = (adjusted_averages / (adjusted_averages.sum())) * (
            1 - creator_proportions - min_proportion
        ) + min_proportion

        # Now, for each transformation source we want to adjust the proportions
        for db_idx, new_prop in zip(transformation_idxs, new_props):
            source_db = steadystate_sources_db[db_idx]
            # BUG: proportions are much lower than they should be.
            logging.info(
                f"Adjusting target proportion for {source_db.name} to {new_prop}"
            )
            source_db.update_flow_target(new_prop)
        logging.info("Finished updating sources")

    # -------------------------------------------------------------------------
    # Core methods that help grab key information about the search
    # -------------------------------------------------------------------------
    # !!! In the following workflows, "deep" refers to the last workflow in the
    # provided subworkflow. These methods are used more frequently as what we
    # really want is the fitness fields saved in that workflows table
    @property
    def subworkflow(self):
        # local import to prevent circular import issues
        from simmate.workflows.utilities import get_workflow

        # Initialize the workflow if a string was given.
        # Otherwise we should already have a workflow class.
        workflow = get_workflow(self.subworkflow_name)

        # BUG: I'll need to rewrite this in the future bc I don't really account
        # for other workflows yet. It would make sense that our workflow changes
        # as the search progresses (e.g. we incorporate DeePMD relaxation once
        # ready)

        return workflow

    @property
    def individuals_datatable(self):
        # NOTE: this table just gives the class back and doesn't filter down
        # to the relevent individuals for this search. For that, use the
        # "individuals" property
        # we assume the table is registered in the local_calcs app
        return self.subworkflow.database_table

    @property
    def individuals(self):
        # note we don't call "all()" on this queryset yet becuase this property
        # it often used as a "base" queryset (and additional filters are added)
        composition = Composition(self.composition)
        return self.individuals_datatable.objects.filter(
            # You'd expect this filter to be...
            #   formula_full=self.composition
            # However, this misses structures that are reduced to a smaller
            # unitcells during relaxation. Therefore, by default, we need to
            # include all individuals that have fewer nsites. This is
            # often what a user wants anyways during searches, so it works out.
            formula_reduced=composition.reduced_formula,
            nsites__lte=composition.num_atoms,
            workflow_name=self.subworkflow_name,
        )

    @property
    def individuals_completed(self):
        # If there is a result for the fitness field, we can treat the calculation as completed
        return self.individuals.filter(**{f"{self.fitness_field}__isnull": False})
        # OPTIMIZE: would it be better to check energy_per_atom or structure_final?
        # Ideally, I could make a relation to the prefect flow run table but this
        # would require a large amount of work to implement.

    # This isn't used anywere
    # @property
    # def individuals_incomplete(self):
    #     datatable = self.subworkflow.database_table
    #     composition = Composition(self.composition)
    #     return datatable.objects.filter(
    #         formula_reduced=composition.reduced_formula,
    #         nsites__lte=composition.num_atoms,
    #         workflow_name=self.subworkflow_name,
    #         finished_at__isnull=True
    #         )

    @property
    def best_individual(self):
        if self.fitness_function == "min":
            # We use order_by to sort from lowest to highest and take the first
            return self.individuals_completed.order_by(self.fitness_field).first()
        if self.fitness_function == "max":
            # We use order_by to order by the negative of our fitness field to
            # get the highest to lowest order and take the first
            return (
                self.individuals_completed.annotate(
                    neg_fitness_field=(-F(f"{self.fitness_field}"))
                )
                .order_by("neg_fitness_field")
                .first()
            )
        if self.fitness_function == "target_value":
            # We calculate the distance from our target value for each item in our
            # fitness field. We use the annotate, Abs, and F methods to do these
            # calculations on the SQL side rather than in python.
            # essentially, annotate makes a temporary "distance" column populated
            # by our absolute difference calculation, then orders it and returns
            # the first value.
            return (
                self.individuals_completed.annotate(
                    distance=functions.Abs(
                        F(f"{self.fitness_field}") - self.target_value
                    )
                )
                .order_by("distance")
                .first()
            )

    def get_nbest_individuals(self, nbest: int):
        if self.fitness_function == "min":
            # We use order_by to sort from lowest to highest and take the first
            return self.individuals_completed.order_by(self.fitness_field)[:nbest]
        if self.fitness_function == "max":
            # We use order_by to order by the negative of our fitness field to
            # get the highest to lowest order and take the first
            return self.individuals_completed.annotate(
                neg_fitness_field=(-F(f"{self.fitness_field}"))
            ).order_by("neg_fitness_field")[:nbest]
        if self.fitness_function == "target_value":
            # We calculate the distance from our target value for each item in our
            # fitness field. We use the annotate, Abs, and F methods to do these
            # calculations on the SQL side rather than in python.
            return self.individuals_completed.annotate(
                distance=functions.Abs(F(f"{self.fitness_field}") - self.target_value)
            ).order_by("distance")[:nbest]

    def get_unique_individuals(
        self,
        use_cache: bool = False,
        as_queryset: bool = False,
    ):
        # get the most-up-to-date results but is slow
        if not use_cache:
            unique = self.validator.get_unique_from_pool()
            # This is an expensive method as the calculation scales, so make sure
            # we cache thes values
            self.unique_individuals_ids = [s.database_object.id for s in unique]
            self.save()

        # OPTIMIZE: this converts back to a queryset object but involves
        # another database query.
        if as_queryset or use_cache:
            unique = (
                self.individuals_completed.filter(id__in=self.unique_individuals_ids)
                .order_by(self.fitness_field)
                .all()
            )

        if not as_queryset and not isinstance(unique, list):
            unique = unique.to_toolkit()

        return unique

    def get_best_individual_history(self):
        """
        Goes through all structures in order that they were created and creates
        a history of which structure was best at any given time.
        """

        individuals = (
            self.individuals_completed.order_by("finished_at")
            .only("id", self.fitness_field)
            .all()
        )

        # Keep a log of the best structures. The first structure to finish is
        # by default the best at that time.
        best_history = [individuals[0].id]
        best_value = getattr(individuals[0], self.fitness_field)
        for individual in individuals:
            potential_new_value = getattr(individual, self.fitness_field)

            if self.fitness_function == "min":
                if potential_new_value < best_value:
                    best_history.append(individual.id)
                    best_value = potential_new_value
            elif self.fitness_function == "max":
                if potential_new_value > best_value:
                    best_history.append(individual.id)
                    best_value = potential_new_value
            elif self.fitness_function == "target_value":
                if abs(potential_new_value - self.target_value) < best_value:
                    best_history.append(individual.id)
                    best_value = potential_new_value

        return best_history

    def write_output_summary(self, directory: Path):
        logging.info(f"Writing search summary to {directory}")

        super().write_output_summary(directory=directory)

        # If the output fails to write, we have a non-critical issue that
        # doesn't affect the search. We therefore don't want to raise an
        # error here -- but instead warn the user and then continue the search
        try:
            # calls all the key methods defined below
            best_cifs_directory = get_directory(directory / "best_structures")
            self.write_best_structures(100, best_cifs_directory)
            unique_cifs_directory = get_directory(directory / "best_structures_unique")
            self.write_unique_structures(unique_cifs_directory)

            self.write_individuals_completed(directory=directory)
            self.write_individuals_completed_full(directory=directory)
            self.write_best_individuals_history(directory=directory)
            self.write_individuals_incomplete(directory=directory)
            self.write_fitness_convergence_plot(directory=directory)
            self.write_fitness_distribution_plot(directory=directory)
            self.write_subworkflow_times_plot(directory=directory)

            # BUG: This is only for "relaxation.vasp.staged", which the assumed
            # workflow for now.
            # !!! Since I've transfered these to a StagedWorkflow base class, I
            # think they should just work so long as the subworkflow inherits it

            self.write_staged_series_convergence_plot(directory=directory)
            self.write_staged_series_histogram_plot(directory=directory)
            self.write_staged_series_times_plot(directory=directory)

            logging.info("Done writing summary.")

        except Exception:
            logging.warning(
                "Failed to write the output summary. This issue will be silenced "
                "to avoid stopping the search. But please report the following "
                "error to our github: https://github.com/jacksund/simmate/issues/"
            )

            # prints the most recent exception traceback
            traceback.print_exc()

    # -------------------------------------------------------------------------
    # Methods for deserializing objects. Consider moving to the toolkit methods
    # -------------------------------------------------------------------------

    @property
    def selector(self):
        # !!! This is largley a copy/paste of the validator method. Consider
        # making a utility to load classes by name

        if hasattr(selector_module, self.selector_name):
            selector_class = getattr(selector_module, self.selector_name)
            selector = selector_class(**self.selector_kwargs)
        else:
            raise Exception("Unknown selector name provided")

        return selector

    @property
    def validator(self):
        # Initialize the fingerprint database
        # For this we need to grab all previously calculated structures of this
        # compositon too pass in too.

        validator_class = getattr(validator_module, self.validator_name)

        logging.info("Generating fingerprints for past structures...")
        fingerprint_validator = validator_class(
            composition=Composition(self.composition),
            structure_pool=self.individuals_completed.order_by(self.fitness_field),
            **self.validator_kwargs,
        )
        logging.info("Done generating fingerprints.")

        # for now I only include final structures that have been calculated
        # OPTIMIZE: should we only do structures that were successfully calculated?
        # If not, there's a chance a structure fails because of something like a
        # crashed slurm job, but it's never submitted again...
        # Or should we only do final structures? Or should I include input
        # structures and even all ionic steps as well...?

        return fingerprint_validator

    # -------------------------------------------------------------------------
    # Writing CSVs summaries and CIFs of best structures
    # -------------------------------------------------------------------------

    def write_best_structures(self, nbest: int, directory: Path):
        best = self.get_nbest_individuals(nbest)
        structures = best.only("structure", "id").to_toolkit()
        self._write_structures(structures, directory)

    def write_unique_structures(self, directory: Path):
        structures = self.get_unique_individuals(use_cache=False)
        self._write_structures(structures, directory)

    # TODO: consider making a utility elsewhere
    def _write_structures(self, structures: list[Structure], directory: Path):
        # if the directory is filled, we need to delete all the files
        # before writing the new ones.
        for file in directory.iterdir():
            try:
                file.unlink()
            except OSError:
                logging.warning("Unable to delete a CIF file: {file}")
                logging.warning(
                    "Updating this directory involves deleting "
                    "and re-writing all CIF files each cycle. If you have a file "
                    "open while this step occurs, then you'll see this warning."
                    "Close your file for this to go away."
                )

        for rank, structure in enumerate(structures):
            rank_cleaned = str(rank).zfill(2)  # converts 1 to 01
            structure_filename = (
                directory
                / f"rank-{str(rank_cleaned)}__id-{structure.database_object.id}.cif"
            )
            structure.to(filename=str(structure_filename), fmt="cif")

    def write_individuals_completed_full(self, directory: Path):
        columns = self.individuals_datatable.get_column_names()
        columns.remove("structure")
        df = self.individuals_completed.defer("structure").to_dataframe(columns)
        csv_filename = directory / "individuals_completed__ALLDATA.csv"
        df.to_csv(csv_filename)

    def write_individuals_completed(self, directory: Path):
        columns = [
            "id",
            f"{self.fitness_field}",
            "finished_at",
            "source",
            "spacegroup__number",
        ]
        df = (
            self.individuals_completed.order_by(self.fitness_field)
            .only(*columns)
            .to_dataframe(columns)
        )
        # label the index column
        df.index.name = "rank"

        # make the timestamps easier to read
        def format_date(date):
            return date.strftime("%Y-%m-%d %H:%M:%S")

        df["finished_at"] = df.finished_at.apply(format_date)

        def format_parents(source):
            return source.get("parent_ids", None) if source else None

        df["parent_ids"] = df.source.apply(format_parents)

        def format_source(source):
            return (
                None
                if not source
                else source.get("creator", None) or source.get("transformation", None)
            )

        df["source"] = df.source.apply(format_source)

        # shorten the column name for easier reading
        df.rename(columns={"spacegroup__number": "spacegroup"}, inplace=True)

        md_filename = directory / "individuals_completed.md"
        df.to_markdown(md_filename)

    def write_best_individuals_history(self, directory: Path):
        columns = ["id", f"{self.fitness_field}", "finished_at"]
        best_history = self.get_best_individual_history()
        df = (
            self.individuals.filter(id__in=best_history)
            .order_by("-finished_at")
            .only(*columns)
            .to_dataframe(columns)
        )

        # make the timestamps easier to read
        def format_date(date):
            return date.strftime("%Y-%m-%d %H:%M:%S")

        df["finished_at"] = df.finished_at.apply(format_date)
        md_filename = directory / "history_of_the_best_individuals.md"
        df.to_markdown(md_filename)

    def write_individuals_incomplete(self, directory: Path):
        structure_sources = self.steadystate_sources.all()
        sources = []
        workitem_ids = []
        statuses = []
        created_at = []
        for source in structure_sources:
            workitem_ids += source.active_workitem_ids
            # as an extra, keep a list of the source names
            sources += [source.name] * len(source.active_workitem_ids)

            for workitem_id in source.active_workitem_ids:
                work_item = WorkItem.objects.get(id=workitem_id)
                statuses.append(work_item.get_status_display())
                created_at.append(work_item.created_at.strftime("%Y-%m-%d %H:%M:%S"))

        df = pandas.DataFrame(
            {
                "workitem_id": workitem_ids,
                "source": sources,
                "status": statuses,
                "created_at": created_at,
            }
        )

        md_filename = directory / "individuals_still_running.md"
        df.to_markdown(md_filename)


class FitnessConvergence(PlotlyFigure):
    def get_plot(search: FixedCompositionSearch):
        # Grab the calculation's structure and convert it to a dataframe
        columns = ["finished_at", search.fitness_field]
        structures_dataframe = search.individuals_completed.only(*columns).to_dataframe(
            columns
        )

        # There's only one plot here, no subplot. So we make the scatter
        # object and just pass it directly to a Figure object
        figure = plotly_express.scatter(
            x=structures_dataframe["finished_at"],
            y=structures_dataframe[search.fitness_field],
            marginal_x="histogram",
            marginal_y="histogram",
        )

        figure.update_layout(
            xaxis_title="Date Completed",
            yaxis_title=(
                "Energy (eV/atom)"
                if search.fitness_field == "energy_per_atom"
                else search.fitness_field
            ),
        )

        return figure


class Correctness(PlotlyFigure):
    def get_plot(
        search: FixedCompositionSearch,
        structure_known: Structure,
    ):
        # load the featurizer from the search object
        featurizer = search.validator.featurizer

        # Grab the calculation's structure and convert it to a dataframe
        structures_dataframe = search.individuals_completed.to_dataframe()

        # because we are using the database model, we first want to convert to
        # pymatgen structures objects and add a column to the dataframe for these
        #
        #   structures_dataframe["structure"] = [
        #       structure.to_toolkit() for structure in ionic_step_structures
        #   ]
        #
        # BUG: the read_frame query creates a new query, so it may be a different
        # length from ionic_step_structures. For this reason, we can't iterate
        # through the queryset like in the commented out code above. Instead,
        # we need to iterate through the dataframe rows.
        # See https://github.com/chrisdev/django-pandas/issues/138 for issue

        structures_dataframe["structure"] = [
            Structure.from_str(s.structure, fmt="POSCAR")
            for _, s in structures_dataframe.iterrows()
        ]

        # generating fingerprints is slow so we use dask to parallelize
        client = get_dask_client()
        logging.info("Submitting to jobs dask...")
        futures = [
            client.submit(featurizer.featurize, s.structure, pure=False)
            for _, s in track(list(structures_dataframe.iterrows()))
        ]
        logging.info("Waiting for dask jobs to finish...")
        structures_dataframe["fingerprint"] = [numpy.array(f.result()) for f in futures]
        logging.info("Done.")

        fingerprint_known = numpy.array(featurizer.featurize(structure_known))

        distances = []
        smallest_distance_id = None
        smallest_distance = 999
        for _, s in structures_dataframe.iterrows():
            distance = numpy.linalg.norm(fingerprint_known - s.fingerprint)
            distances.append(distance)

            # import scipy
            # scipy.spatial.distance.cosine(fingerprint_known, s.fingerprint)
            # BUG: I assume distance method. I need to check the validator in
            # case the method prefers something like cosine distance.

            if distance < smallest_distance:
                smallest_distance = distance
                smallest_distance_id = s.id
        logging.info(
            f"The most similar structure is id={smallest_distance_id} "
            f"with distance {smallest_distance:.3f}"
        )
        structures_dataframe["fingerprint_distance"] = distances

        # There's only one plot here, no subplot. So we make the scatter
        # object and just pass it directly to a Figure object
        scatter = plotly_go.Scatter(
            x=structures_dataframe["finished_at"],
            y=structures_dataframe["fingerprint_distance"],
            mode="markers",
            # BUG: Does this need to be fitness_field instead of energy?
            marker_color=structures_dataframe["energy_per_atom"],
        )
        figure = plotly_go.Figure(data=scatter)

        figure.update_layout(
            xaxis_title="Date Completed",
            yaxis_title="Distance from Known Structure",
        )

        return figure


class SubworkflowTimes(PlotlyFigure):
    def get_plot(search: FixedCompositionSearch):
        # Grab the calculation's structure and convert it to a dataframe
        data = search.individuals_completed.values_list(
            "total_time", "queue_time"
        ).all()

        # time is stored in seconds and we convert to minutes
        total_times = [e[0] / 60 for e in data]
        # queue_times = [e[1] / 60 for e in data]

        figure = plotly_go.Figure()
        hist_1 = plotly_go.Histogram(x=total_times)  # , name="Total run time (min)"
        # hist_2 = plotly_go.Histogram(x=queue_times, name="Total queue time (min)")
        figure.add_trace(hist_1)
        # figure.add_trace(hist_2)
        figure.update_layout(
            xaxis_title="Total calculation time (min)",
            yaxis_title="Individuals (#)",
            barmode="overlay",
        )
        # figure.update_traces(opacity=0.75)
        return figure


class FitnessDistribution(PlotlyFigure):
    def get_plot(search: FixedCompositionSearch):
        # Grab the calculation's structure and convert it to a dataframe
        structures_dataframe = search.individuals_completed.only(
            search.fitness_field
        ).to_dataframe([search.fitness_field])

        # There's only one plot here, no subplot. So we make the scatter
        # object and just pass it directly to a Figure object
        histogram = plotly_go.Histogram(
            x=structures_dataframe[search.fitness_field],
        )
        figure = plotly_go.Figure(data=histogram)

        figure.update_layout(
            xaxis_title=(
                "Energy (eV/atom)"
                if search.fitness_field == "energy_per_atom"
                else search.fitness_field
            ),
            yaxis_title="Individuals (#)",
        )

        return figure


class StagedSeriesConvergence(PlotlyFigure):
    def get_plot(search: FixedCompositionSearch):
        composition = Composition(search.composition)
        plot = search.subworkflow.get_staged_series_convergence_plot(
            # See `individuals` method for why we use these filters
            formula_reduced=composition.reduced_formula,
            nsites__lte=composition.num_atoms,
            **{f"{search.fitness_field}__isnull": False},
            fitness_field=search.fitness_field,
        )
        return plot


class StagedSeriesHistogram(PlotlyFigure):
    def get_plot(search: FixedCompositionSearch):
        composition = Composition(search.composition)
        plot = search.subworkflow.get_staged_series_histogram_plot(
            # See `individuals` method for why we use these filters
            formula_reduced=composition.reduced_formula,
            nsites__lte=composition.num_atoms,
            **{f"{search.fitness_field}__isnull": False},
            fitness_field=search.fitness_field,
        )
        return plot


class StagedSeriesTimes(PlotlyFigure):
    def get_plot(search: FixedCompositionSearch):
        composition = Composition(search.composition)
        plot = search.subworkflow.get_staged_series_times_plot(
            # See `individuals` method for why we use these filters
            formula_reduced=composition.reduced_formula,
            nsites__lte=composition.num_atoms,
            **{f"{search.fitness_field}__isnull": False},
        )
        return plot


# register all plotting methods to the database table
for _plot in [
    FitnessConvergence,
    Correctness,
    FitnessDistribution,
    SubworkflowTimes,
    StagedSeriesConvergence,
    StagedSeriesHistogram,
    StagedSeriesTimes,
]:
    _plot.register_to_class(FixedCompositionSearch)
