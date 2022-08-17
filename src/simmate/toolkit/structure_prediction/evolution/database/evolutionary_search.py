# -*- coding: utf-8 -*-

import logging
from pathlib import Path

import pandas
import plotly.graph_objects as plotly_go

from simmate.database.base_data_types import DatabaseTable, table_column
from simmate.toolkit import Composition
from simmate.toolkit.structure_prediction.evolution.database import StructureSource
from simmate.utilities import get_directory
from simmate.workflow_engine.execution import WorkItem


class EvolutionarySearch(DatabaseTable):
    """
    This database table holds all of the information related to an evolutionary
    search and also has convient methods to analyze the data + write output files.
    """

    class Meta:
        app_label = "workflows"

    # !!! consider making a composition-based mixin
    composition = table_column.CharField(max_length=50)

    # Import path for the workflow and the database table of results
    subworkflow_name = table_column.CharField(max_length=200)
    subworkflow_kwargs = table_column.JSONField(default={})
    fitness_field = table_column.CharField(max_length=200)

    # Other settings for the search
    max_structures = table_column.IntegerField()
    limit_best_survival = table_column.IntegerField()
    nfirst_generation = table_column.IntegerField()
    nsteadystate = table_column.IntegerField()

    # Key classes to use during the search
    selector_name = table_column.CharField(max_length=200)
    selector_kwargs = table_column.JSONField(default={})
    validator_name = table_column.CharField(max_length=200)
    validator_kwargs = table_column.JSONField(default={})
    # stop_condition_name ---> assumed for now
    # information about the singleshot_sources and steadystate_sources
    # are stored within the IndividualSources datatable

    # Tags to submit the NewIndividual workflow with. Should be a list of strings
    tags = table_column.JSONField()

    # the time to sleep between file writing and steady-state checks.
    sleep_step = table_column.FloatField()

    # disable the source column
    source = None

    # TODO: maybe accept an input for an expected structure in order to allow
    # creation of plots that show convergence vs. the expected. Will be very
    # useful benchmarking and when the user has a target structure that they
    # hope to see.
    # expected_structure = table_column.JSONField()

    # -------------------------------------------------------------------------
    # Highest-level methods that run the overall search
    # -------------------------------------------------------------------------

    def check_stop_condition(self):

        # first see if we've hit our maximum limit for structures.
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
        # The 2nd stop condition is based on how long we've have the same
        # "best" individual. If the number of new individuals calculated (without
        # any becoming the new "best") is greater than limit_best_survival, then
        # we can stop the search.

        # grab the best individual for reference
        best = self.best_individual

        # We need this if-statement in case no structures have completed yet.
        if not best:
            return False

        # count the number of new individuals added AFTER the best one. If it is
        # more than limit_best_survival, we stop the search.
        num_new_structures_since_best = self.individuals.filter(
            # check energies to ensure we only count completed calculations
            energy_per_atom__gt=best.energy_per_atom,
            created_at__gte=best.created_at,
        ).count()
        if num_new_structures_since_best > self.limit_best_survival:
            logging.info(
                "Best individual has not changed after "
                f"{self.limit_best_survival} new individuals added."
            )
            return True
        # If we reached this point, then we haven't hit a stop condition yet!
        return False

    def _check_singleshot_sources(self, directory: Path):
        logging.warning(
            "Singleshot sources is still in testing. The found structures "
            "are not submitted as part of the search."
        )

        try:

            from simmate.toolkit.structure_prediction import (
                get_known_structures,
                get_structures_from_prototypes,
                get_structures_from_substitution_of_known,
            )

            composition = Composition(self.composition)

            structures_known = get_known_structures(
                composition,
                strict_nsites=True,
            )
            logging.info(
                f"Generated {len(structures_known)} structures from other databases"
            )
            directory_known = get_directory(directory / "known_structures")
            for i, s in enumerate(structures_known):
                s.to("cif", directory_known / f"{i}.cif")

            structures_sub = get_structures_from_substitution_of_known(
                composition,
                strict_nsites=True,
            )
            logging.info(
                f"Generated {len(structures_sub)} structures from substitutions"
            )
            directory_sub = get_directory(directory / "from_substitutions")
            for i, s in enumerate(structures_sub):
                s.to("cif", directory_sub / f"{i}.cif")

            structures_prototype = get_structures_from_prototypes(
                composition,
                max_sites=int(composition.num_atoms),
            )
            logging.info(
                f"Generated {len(structures_prototype)} structures from prototypes"
            )
            directory_sub = get_directory(directory / "from_prototypes")
            for i, s in enumerate(structures_prototype):
                s.to("cif", directory_sub / f"{i}.cif")

        except Exception as error:
            logging.error(
                f"Singleshot sources failed with {self.composition}. "
                "Please report this issue."
            )
            raise error

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

    def _init_steadystate_sources_to_db(self, steadystate_sources):
        composition = Composition(self.composition)

        # Initialize the steady-state sources, which are given as a list of
        # (proportion, class/class_str, kwargs) for each. As we go through
        # these, we also collect the proportion list for them.
        steadystate_sources_cleaned = []
        steadystate_source_proportions = []
        for proportion, source_name in steadystate_sources:

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
            logging.warning(
                "fractions for steady-state sources do not add to 1."
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

            source_db = StructureSource(
                name=source_name,
                # kwargs --> default for now,
                is_steadystate=True,
                is_singleshot=False,
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
            StructurePrediction__Python__NewIndividual,
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
        steadystate_sources_db = self.structure_sources.filter(
            is_steadystate=True
        ).all()
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
                logging.info(f"Submitting new individuals from {source_db.name}")

            for n in range(nflows_to_submit):

                # submit the workflow for the new individual. Note, the structure
                # won't be evuluated until the job actually starts. This allows
                # our validator to have the most current information available
                # when starting the structure creation
                state = StructurePrediction__Python__NewIndividual.run_cloud(
                    search_id=self.id,
                    structure_source_id=source_db.id,
                )

                # Attached the id to our source so we know how many
                # associated jobs are running.
                # NOTE: this is the WorkItem id and NOT the run_id!!!
                source_db.workitem_ids.append(state.pk)
                source_db.save()

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
        return self.individuals_datatable.objects.filter(
            formula_full=self.composition,
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

        # calls all the key methods defined below
        best_cifs_directory = get_directory(directory / "best_structures_cifs")
        self.write_best_structures(100, best_cifs_directory)
        self.write_individuals_completed(directory)
        self.write_individuals_completed_full(directory)
        self.write_best_individuals_history(directory)
        self.write_individuals_incomplete(directory)
        self.write_convergence_plot(directory)
        self.write_final_fitness_plot(directory)
        self.write_subworkflow_times_plot(directory)

        # BUG: This is only for "relaxation.vasp.staged", which the assumed
        # workflow for now.
        self.subworkflow.write_series_convergence_plot(
            directory=directory,
            formula_full=self.composition,
            energy_per_atom__isnull=False,
        )

        logging.info("Done writing summary.")

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
        import logging

        from simmate.toolkit import Composition
        from simmate.toolkit.validators.fingerprint.pcrystalnn import (
            PartialCrystalNNFingerprint,
        )

        logging.info("Generating fingerprints for past structures...")
        fingerprint_validator = PartialCrystalNNFingerprint(
            composition=Composition(self.composition),
            structure_pool=self.individuals,
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
            file.unlink()

        best = self.get_nbest_indiviudals(nbest)
        structures = best.only("structure_string", "id").to_toolkit()
        for rank, structure in enumerate(structures):
            structure_filename = (
                directory / f"rank-{rank}__id-{structure.database_object.id}.cif"
            )
            structure.to("cif", structure_filename)

    def write_individuals_completed_full(self, directory: Path):
        columns = self.individuals_datatable.get_column_names()
        columns.remove("structure_string")
        df = self.individuals_completed.defer("structure_string").to_dataframe(columns)
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
            return source.get("parent_ids", None)

        df["parent_ids"] = df.source.apply(format_parents)

        def format_source(source):
            return source.get("creator", None) or source.get("transformation", None)

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
        structure_sources = self.structure_sources.all()
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

    # -------------------------------------------------------------------------
    # Generating plots
    # -------------------------------------------------------------------------

    def get_convergence_plot(self):

        # Grab the calculation's structure and convert it to a dataframe
        columns = ["updated_at", self.fitness_field]
        structures_dataframe = self.individuals_completed.only(*columns).to_dataframe(
            columns
        )

        # There's only one plot here, no subplot. So we make the scatter
        # object and just pass it directly to a Figure object
        scatter = plotly_go.Scatter(
            x=structures_dataframe["updated_at"],
            y=structures_dataframe[self.fitness_field],
            mode="markers",
        )
        figure = plotly_go.Figure(data=scatter)

        figure.update_layout(
            xaxis_title="Date Completed",
            yaxis_title="Energy (eV/atom)"
            if self.fitness_field == "energy_per_atom"
            else self.fitness_field,
        )

        # we return the figure object for the user
        return figure

    def view_convergence_plot(self):
        figure = self.get_convergence_plot()
        figure.show(renderer="browser")

    def write_convergence_plot(self, directory: Path):
        figure = self.get_convergence_plot()
        figure.write_html(
            directory / f"convergence__time_vs_{self.fitness_field}.html",
            include_plotlyjs="cdn",
        )

    def get_correctness_plot(self, structure_known):

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
            [element.symbol for element in Composition(self.composition).elements]
        )
        # --------------------------------------------------------

        # Grab the calculation's structure and convert it to a dataframe
        structures_dataframe = self.individuals_completed.to_dataframe()

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
            Structure.from_str(s.structure_string, fmt="POSCAR")
            for _, s in structures_dataframe.iterrows()
        ]

        from tqdm import tqdm

        structures_dataframe["fingerprint"] = [
            numpy.array(featurizer.featurize(s.structure))
            for _, s in tqdm(structures_dataframe.iterrows())
        ]

        fingerprint_known = numpy.array(featurizer.featurize(structure_known))

        structures_dataframe["fingerprint_distance"] = [
            numpy.linalg.norm(fingerprint_known - s.fingerprint)
            for _, s in tqdm(structures_dataframe.iterrows())
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

        # we return the figure object for the user
        return figure

    def view_correctness_plot(self, structure_known):
        figure = self.get_correctness_plot(structure_known)
        figure.show(renderer="browser")

    def write_correctness_plot(self, structure_known, directory: Path):
        figure = self.get_convergence_plot()
        figure.write_html(
            directory / "convergence__time_vs_fingerprint_distance.html",
            include_plotlyjs="cdn",
        )

    # -------------------------------------------------------------------------
    # This plot is specifically for "relaxation.vasp.staged" and should be moved
    # to that class when this search allows new workflows
    # -------------------------------------------------------------------------

    def get_final_fitness_plot(self):

        # Grab the calculation's structure and convert it to a dataframe
        structures_dataframe = self.individuals_completed.only(
            self.fitness_field
        ).to_dataframe(self.fitness_field)

        # There's only one plot here, no subplot. So we make the scatter
        # object and just pass it directly to a Figure object
        histogram = plotly_go.Histogram(
            x=structures_dataframe[self.fitness_field],
        )
        figure = plotly_go.Figure(data=histogram)

        figure.update_layout(
            xaxis_title="Energy (eV/atom)"
            if self.fitness_field == "energy_per_atom"
            else self.fitness_field,
            yaxis_title="Individuals (#)",
        )

        # we return the figure object for the user
        return figure

    def view_final_fitness_plot(self):
        figure = self.get_final_fitness_plot()
        figure.show(renderer="browser")

    def write_final_fitness_plot(self, directory: Path):
        figure = self.get_final_fitness_plot()
        figure.write_html(
            directory / f"distribution_of_{self.fitness_field}.html",
            include_plotlyjs="cdn",
        )

    def get_subworkflow_times_plot(self):

        # Grab the calculation's structure and convert it to a dataframe
        columns = ["created_at", "updated_at"]
        df = self.individuals_completed.only(*columns).to_dataframe(columns)
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

    def view_subworkflow_times_plot(self):
        figure = self.get_subworkflow_times_plot()
        figure.show(renderer="browser")

    def write_subworkflow_times_plot(self, directory: Path):
        figure = self.get_subworkflow_times_plot()
        figure.write_html(
            directory / "distribution_of_subworkflow_times.html",
            include_plotlyjs="cdn",
        )
