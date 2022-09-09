# -*- coding: utf-8 -*-

import logging
import math
import traceback
from pathlib import Path

import pandas
import plotly.graph_objects as plotly_go
from rich.progress import track

from simmate.database.base_data_types import Calculation, table_column
from simmate.toolkit import Composition, Structure
from simmate.toolkit.structure_prediction.evolution.database import SteadystateSource
from simmate.toolkit.validators import fingerprint as validator_module
from simmate.utilities import get_directory
from simmate.visualization.plotting import PlotlyFigure
from simmate.workflow_engine.execution import WorkItem


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
        # {f"{self.fitness_field}__isnull"=False} # when I allow other fitness fxns
        count_exact = self.individuals_datatable.objects.filter(
            formula_full=self.composition,
            workflow_name=self.subworkflow_name,
            energy_per_atom__isnull=False,
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
        num_new_structures_since_best = self.individuals.filter(
            energy_per_atom__gt=best.energy_per_atom + self.convergence_cutoff,
            created_at__gte=best.created_at,
        ).count()
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
        from simmate.toolkit.structure_prediction.evolution.workflows.utilities import (
            write_and_submit_structures,
        )
        from simmate.toolkit.structure_prediction.known import get_known_structures
        from simmate.toolkit.structure_prediction.prototypes import (
            get_structures_from_prototypes,
        )
        from simmate.toolkit.structure_prediction.substitution import (
            get_structures_from_substitution_of_known,
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
        # While these are percent values, we want specific counts. We convert to
        # those here.
        steadystate_source_counts = [
            int(p * self.nsteadystate) for p in steadystate_source_proportions
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
                nsteadystate_target=ntarget_jobs,
                search=self,
            )
            source_db.save()
            steadystate_sources_db.append(source_db)
        # !!! What if this search has been ran before or a matching search is
        # being ran elsewhere? Do we still want new entries for each?

        return steadystate_sources_db

    def _check_steadystate_workflows(self):

        # local import to prevent circular import issues
        from simmate.toolkit.structure_prediction.evolution.workflows.new_individual import (
            StructurePrediction__Toolkit__NewIndividual,
        )

        # transformations from a database table require that we have
        # completed structures in the database. We want to wait until there's
        # a set amount before we start mutating the best. We check that here.
        if self.individuals_completed.count() < self.nfirst_generation:
            logging.info(
                "Search hasn't finished nfirst_generation yet "
                f"({self.nfirst_generation} individuals). "
                "Skipping transformations."
            )
            ready_for_transformations = False
        else:
            ready_for_transformations = True

        # we iterate through each steady-state source and check to see how many
        # jobs are still running for it. If it's less than the target steady-state,
        # then we need to submit more!
        steadystate_sources_db = self.steadystate_sources.all()
        for source_db in steadystate_sources_db:

            # skip if we have a transformation but aren't ready for it yet
            if source_db.is_transformation and not ready_for_transformations:
                continue

            # This loop says for the number of steady state runs we are short,
            # create that many new individuals! max(x,0) ensure we don't get a
            # negative value. A value of 0 means we are at steady-state and can
            # just skip this loop.
            nflows_to_submit = max(
                int(source_db.nsteadystate_target - source_db.nflow_runs), 0
            )

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
                )

                # Attached the id to our source so we know how many
                # associated jobs are running.
                # NOTE: this is the WorkItem id and NOT the run_id!!!
                source_db.workitem_ids.append(state.pk)
                source_db.save()

            # reactivate logging
            logger.disabled = False

    # -------------------------------------------------------------------------
    # Core methods that help grab key information about the search
    # -------------------------------------------------------------------------

    @property
    def subworkflow(self):

        # local import to prevent circular import issues
        from simmate.workflows.utilities import get_workflow

        # Initialize the workflow if a string was given.
        # Otherwise we should already have a workflow class.
        if self.subworkflow_name == "relaxation.vasp.staged":
            workflow = get_workflow(self.subworkflow_name)
        else:
            raise Exception(
                "Only `relaxation.vasp.staged` is supported in early testing"
            )

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
        # If there is an energy_per_atom, we can treat the calculation as completed
        return self.individuals.filter(energy_per_atom__isnull=False)
        # OPTIMIZE: would it be better to check energy_per_atom or structure_final?
        # Ideally, I could make a relation to the prefect flow run table but this
        # would require a large amount of work to implement.

    @property
    def individuals_incomplete(self):
        # If there is an energy_per_atom, we can treat the calculation as completed
        return self.individuals.filter(energy_per_atom__isnull=True)

    @property
    def best_individual(self):
        return self.individuals_completed.order_by(self.fitness_field).first()

    def get_nbest_indiviudals(self, nbest: int):
        return self.individuals_completed.order_by(self.fitness_field)[:nbest]

    def get_best_individual_history(self):
        """
        Goes through all structures in order that they were created and creates
        a history of which structure was best at any given time.
        """

        individuals = (
            self.individuals_completed.order_by("updated_at")
            .only("id", self.fitness_field)
            .all()
        )

        # Keep a log of the best structures. The first structure to finish is
        # by default the best at that time.
        best_history = [individuals[0].id]
        best_value = getattr(individuals[0], self.fitness_field)
        for individual in individuals:
            potential_new_value = getattr(individual, self.fitness_field)

            # BUG: I assume lower is better, but this may change
            if potential_new_value < best_value:
                best_history.append(individual.id)
                best_value = potential_new_value

        return best_history

    def write_summary(self, directory: Path):
        logging.info(f"Writing search summary to {directory}")

        super().write_output_summary(directory=directory)

        # If the output fails to write, we have a non-critical issue that
        # doesn't affect the search. We therefore don't want to raise an
        # error here -- but instead warn the user and then continue the search
        try:
            # calls all the key methods defined below
            best_cifs_directory = get_directory(directory / "best_structures_cifs")
            self.write_best_structures(100, best_cifs_directory)
            self.write_individuals_completed(directory=directory)
            self.write_individuals_completed_full(directory=directory)
            self.write_best_individuals_history(directory=directory)
            self.write_individuals_incomplete(directory=directory)
            self.write_fitness_convergence_plot(directory=directory)
            self.write_fitness_distribution_plot(directory=directory)
            self.write_subworkflow_times_plot(directory=directory)

            # BUG: This is only for "relaxation.vasp.staged", which the assumed
            # workflow for now.
            composition = Composition(self.composition)
            self.subworkflow.write_staged_series_convergence_plot(
                directory=directory,
                # See `individuals` method for why we use these filters
                formula_reduced=composition.reduced_formula,
                nsites__lte=composition.num_atoms,
                energy_per_atom__isnull=False,
            )
            self.subworkflow.write_staged_series_histogram_plot(
                directory=directory,
                # See `individuals` method for why we use these filters
                formula_reduced=composition.reduced_formula,
                nsites__lte=composition.num_atoms,
                energy_per_atom__isnull=False,
            )

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

        # Initialize the selector
        if self.selector_name == "TruncatedSelection":
            from simmate.toolkit.structure_prediction.evolution.selectors import (
                TruncatedSelection,
            )

            selector = TruncatedSelection()
        else:  # BUG
            raise Exception("We only support TruncatedSelection right now")

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
            structure_pool=self.individuals,
            **self.validator_kwargs,
        )
        logging.info("Done generating fingerprints.")

        # BUG: should we only do structures that were successfully calculated?
        # If not, there's a chance a structure fails because of something like a
        # crashed slurm job, but it's never submitted again...
        # OPTIMIZE: should we only do final structures? Or should I include input
        # structures and even all ionic steps as well...?
        return fingerprint_validator

    # -------------------------------------------------------------------------
    # Writing CSVs summaries and CIFs of best structures
    # -------------------------------------------------------------------------

    def write_best_structures(self, nbest: int, directory: Path):
        # if the directory is filled, we need to delete all the files
        # before writing the new ones.
        for file in directory.iterdir():
            try:
                file.unlink()
            except OSError:
                logging.warning("Unable to delete a CIF file: {file}")
                logging.warning(
                    "Updating the 'best structures' directory involves deleting "
                    "and re-writing all CIF files each cycle. If you have a file "
                    "open while this step occurs, then you'll see this warning."
                    "Close your file for this to go away."
                )

        best = self.get_nbest_indiviudals(nbest)
        structures = best.only("structure", "id").to_toolkit()
        for rank, structure in enumerate(structures):
            rank_cleaned = str(rank).zfill(2)  # converts 1 to 01
            structure_filename = (
                directory
                / f"rank-{str(rank_cleaned)}__id-{structure.database_object.id}.cif"
            )
            structure.to("cif", structure_filename)

    def write_individuals_completed_full(self, directory: Path):
        columns = self.individuals_datatable.get_column_names()
        columns.remove("structure")
        df = self.individuals_completed.defer("structure").to_dataframe(columns)
        csv_filename = directory / "individuals_completed__ALLDATA.csv"
        df.to_csv(csv_filename)

    def write_individuals_completed(self, directory: Path):
        columns = [
            "id",
            "energy_per_atom",
            "updated_at",
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

        df["updated_at"] = df.updated_at.apply(format_date)

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
        columns = ["id", "energy_per_atom", "updated_at"]
        best_history = self.get_best_individual_history()
        df = (
            self.individuals.filter(id__in=best_history)
            .order_by("-updated_at")
            .only(*columns)
            .to_dataframe(columns)
        )

        # make the timestamps easier to read
        def format_date(date):
            return date.strftime("%Y-%m-%d %H:%M:%S")

        df["updated_at"] = df.updated_at.apply(format_date)
        md_filename = directory / "history_of_the_best_individuals.md"
        df.to_markdown(md_filename)

    def write_individuals_incomplete(self, directory: Path):
        structure_sources = self.steadystate_sources.all()
        sources = []
        workitem_ids = []
        statuses = []
        created_at = []
        for source in structure_sources:
            workitem_ids += source.workitem_ids
            # as an extra, keep a list of the source names
            sources += [source.name] * len(source.workitem_ids)

            for workitem_id in source.workitem_ids:
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
        columns = ["updated_at", search.fitness_field]
        structures_dataframe = search.individuals_completed.only(*columns).to_dataframe(
            columns
        )

        # There's only one plot here, no subplot. So we make the scatter
        # object and just pass it directly to a Figure object
        scatter = plotly_go.Scatter(
            x=structures_dataframe["updated_at"],
            y=structures_dataframe[search.fitness_field],
            mode="markers",
        )
        figure = plotly_go.Figure(data=scatter)

        figure.update_layout(
            xaxis_title="Date Completed",
            yaxis_title="Energy (eV/atom)"
            if search.fitness_field == "energy_per_atom"
            else search.fitness_field,
        )

        return figure


class Correctness(PlotlyFigure):
    def get_plot(
        search: FixedCompositionSearch,
        structure_known: Structure,
    ):

        # --------------------------------------------------------
        # This code is from simmate.toolkit.validators.fingerprint.pcrystalnn
        # OPTIMIZE: There should be a convience method to make this featurizer
        # since I use it so much
        import numpy
        from matminer.featurizers.site import CrystalNNFingerprint
        from matminer.featurizers.structure.sites import (  # PartialsSiteStatsFingerprint,
            SiteStatsFingerprint,
        )

        from simmate.toolkit import Composition

        sitefingerprint_method = CrystalNNFingerprint.from_preset(
            "ops", distance_cutoffs=None, x_diff_weight=3
        )
        featurizer = SiteStatsFingerprint(
            sitefingerprint_method,
            stats=["mean", "std_dev", "minimum", "maximum"],
        )
        featurizer.elements_ = numpy.array(
            [element.symbol for element in Composition(search.composition).elements]
        )
        # --------------------------------------------------------

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
        from simmate.toolkit import Structure

        structures_dataframe["structure"] = [
            Structure.from_str(s.structure, fmt="POSCAR")
            for _, s in structures_dataframe.iterrows()
        ]

        structures_dataframe["fingerprint"] = [
            numpy.array(featurizer.featurize(s.structure))
            for _, s in track(structures_dataframe.iterrows())
        ]

        fingerprint_known = numpy.array(featurizer.featurize(structure_known))

        structures_dataframe["fingerprint_distance"] = [
            numpy.linalg.norm(fingerprint_known - s.fingerprint)
            for _, s in track(structures_dataframe.iterrows())
        ]

        # There's only one plot here, no subplot. So we make the scatter
        # object and just pass it directly to a Figure object
        scatter = plotly_go.Scatter(
            x=structures_dataframe["updated_at"],
            y=structures_dataframe["fingerprint_distance"],
            mode="markers",
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
        columns = ["created_at", "updated_at"]
        df = search.individuals_completed.only(*columns).to_dataframe(columns)
        df["total_time"] = df.updated_at - df.created_at

        def convert_to_min(time):
            # time is stored in nanoseconds and we convert to minutes
            return time.value * (10**-9) / 60

        df["total_time_min"] = df.total_time.apply(convert_to_min)
        histogram = plotly_go.Histogram(x=df.total_time_min)
        figure = plotly_go.Figure(data=histogram)
        figure.update_layout(
            xaxis_title="Total time (min)",
            yaxis_title="Individuals (#)",
        )
        return figure


class FitnessDistribution(PlotlyFigure):
    def get_plot(search: FixedCompositionSearch):

        # Grab the calculation's structure and convert it to a dataframe
        structures_dataframe = search.individuals_completed.only(
            search.fitness_field
        ).to_dataframe(search.fitness_field)

        # There's only one plot here, no subplot. So we make the scatter
        # object and just pass it directly to a Figure object
        histogram = plotly_go.Histogram(
            x=structures_dataframe[search.fitness_field],
        )
        figure = plotly_go.Figure(data=histogram)

        figure.update_layout(
            xaxis_title="Energy (eV/atom)"
            if search.fitness_field == "energy_per_atom"
            else search.fitness_field,
            yaxis_title="Individuals (#)",
        )

        return figure


# register all plotting methods to the database table
for _plot in [
    FitnessConvergence,
    Correctness,
    FitnessDistribution,
    SubworkflowTimes,
]:
    _plot.register_to_class(FixedCompositionSearch)
