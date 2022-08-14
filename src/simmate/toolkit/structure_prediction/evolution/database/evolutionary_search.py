# -*- coding: utf-8 -*-

import plotly.graph_objects as plotly_go

from simmate.database.base_data_types import table_column, DatabaseTable


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
            workflow_name="relaxation.vasp.quality04",  # BUG: self.subworkflow_name,
        )

    @property
    def individuals_completed(self):
        # If there is an energy_per_atom, we can treat the calculation as completed
        return self.individuals.filter(energy_per_atom__isnull=False)
        # OPTIMIZE: would it be better to check energy_per_atom or structure_final?
        # Ideally, I could make a relation to the prefect flow run table but this
        # would require a large amount of work to implement.

    @property
    def individual_best(self):
        best = self.individuals_completed.order_by("energy_per_atom").first()
        return best

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

    def get_convergence_plot(self):

        # Grab the calculation's structure and convert it to a dataframe
        structures_dataframe = self.individuals_completed.to_dataframe()

        # There's only one plot here, no subplot. So we make the scatter
        # object and just pass it directly to a Figure object
        scatter = plotly_go.Scatter(
            x=structures_dataframe["updated_at"],
            y=structures_dataframe["energy_per_atom"],
            mode="markers",
        )
        figure = plotly_go.Figure(data=scatter)

        figure.update_layout(
            xaxis_title="Date Completed",
            yaxis_title="Energy (eV/atom)",
        )

        # we return the figure object for the user
        return figure

    def view_convergence_plot(self):
        figure = self.get_convergence_plot()
        figure.show(renderer="browser")

    def get_correctness_plot(self, structure_known):

        # --------------------------------------------------------
        # This code is from simmate.toolkit.validators.fingerprint.pcrystalnn
        # OPTIMIZE: There should be a convience method to make this featurizer
        # since I use it so much
        import numpy
        from simmate.toolkit import Composition
        from matminer.featurizers.site import CrystalNNFingerprint
        from matminer.featurizers.structure.sites import (
            SiteStatsFingerprint,  # PartialsSiteStatsFingerprint,
        )

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
