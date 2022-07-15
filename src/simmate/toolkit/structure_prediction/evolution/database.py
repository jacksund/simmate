# -*- coding: utf-8 -*-

import plotly.graph_objects as plotly_go
from django.apps import apps as django_apps
from prefect.client import get_client
from prefect.orion.schemas.filters import FlowRunFilter

from simmate.database.base_data_types import table_column, DatabaseTable
from simmate.utilities import async_to_sync


class EvolutionarySearch(DatabaseTable):
    """
    This database table holds all of the information related to an evolutionary
    search and also has convient methods to analyze the data.

    Loading Results
    ---------------

    Typically, you'll load your search through a search id or a composition:

    .. code-block:: python

        from simmate.shortcuts import SearchResults

        # if you know the id
        search_results = SearchResults.objects.get(id=123)

        # if you know the composition
        search_results = SearchResults.objects.get(id="Ca2 N1")

    Alternatively, you can find these out by looking at a table of all the
    evolutionary searches that have been ran:

    .. code-block:: python

        all_searches = SearchResults.objects.to_dataframe()

    Viewing Results
    ---------------

    The first thing you may want to check is the best structure found. To access
    this and write it to a file:

    .. code-block:: python

        # loads the best structure and converts it to a pymatgen structure object
        structure = search_results.best_individual.to_toolkit()

        # writes it to a cif file
        structure.to("cif", "best_structure.cif")

    To view convergence of the search, you can use the convenient plotting methods.

    Note: this will open up the plot in your default browser, so this command
    won't work properly through an ssh terminal.

    .. code-block:: python

        search_results.view_convergence_plot()

    If you are benchmarking Simmate to see if it found a particular structure,
    you can use:

    .. code-block:: python

        from simmate.toolkit import Structure

        structure = Structure.from_file("example123.cif")

        search_results.view_correctness_plot(structure)

    Beyond plots, you can also access a table of all calculated structures:

    .. code-block:: python

        dataframe = search_results.individuals_completed.to_dataframe()


    """

    class Meta:
        app_label = "workflows"

    # consider formula_full or chemical_system by making a composition-based mixin
    composition = table_column.CharField(max_length=50)  # !!! change to formula_full?

    # Import path for the workflow(s)
    individuals_datatable_str = table_column.CharField(max_length=200)

    # List of import paths for workflows used at any point. While all workflows
    # populate the individuals_datatable, they might do this in different ways.
    # For example, one may start with a ML prediction, another runs a series
    # of VASP relaxations, and another simply copies a structure from AFLOW.
    workflows = table_column.JSONField()

    # Import path that grabs the fitness value
    # I assume energy for now
    # fitness_function = table_column.CharField(max_length=200)

    max_structures = table_column.IntegerField()
    limit_best_survival = table_column.IntegerField()

    # relationships
    # sources / individuals
    # stop_conditions

    # get_stats:
    #   Total structure counts
    #   makeup of random, heredity, mutation, seeds, COPEX

    @property
    def individuals_datatable(self):
        # NOTE: this table just gives the class back and doesn't filter down
        # to the relevent individuals for this search. For that, use the "individuals"
        # property
        # we assume the table is registered in the local_calcs app
        return django_apps.get_model(
            app_label="workflows",
            model_name=self.individuals_datatable_str,
        )

    @property
    def individuals(self):
        # note we don't call "all()" on this queryset yet becuase this property
        # it often used as a "base" queryset (and additional filters are added)
        return self.individuals_datatable.objects.filter(formula_full=self.composition)

    @property
    def individuals_completed(self):
        # If there is an energy_per_atom, we can treat the calculation as completed
        return self.individuals.filter(energy_per_atom__isnull=False)
        # OPTIMIZE: would it be better to check energy_per_atom or structure_final?
        # Ideally, I could make a relation to the prefect flow run table but this
        # would require a large amount of work to implement.

    @property
    def best_individual(self):
        best = self.individuals_completed.order_by("energy_per_atom").first()
        return best

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


class StructureSource(DatabaseTable):
    class Meta:
        app_label = "workflows"

    name = table_column.CharField(max_length=50)

    is_steadystate = table_column.BooleanField()
    is_singleshot = table_column.BooleanField()

    settings = table_column.JSONField(default=dict)

    # This list limits to ids that are submitted or running
    prefect_flow_run_ids = table_column.JSONField(default=list)

    search = table_column.ForeignKey(
        EvolutionarySearch,
        on_delete=table_column.CASCADE,
        related_name="sources",
    )

    @staticmethod
    @async_to_sync
    async def _check_still_running_ids(prefect_flow_run_ids):
        """
        Queries Prefect to see check on a list of flow run ids and determines
        which ones are still in a scheduled, running, or pending state.
        From the list of ids given, it will return a list of the ones that
        haven't finished yet.

        This is normally used within `update_flow_run_ids` and shouldn't
        be called directly.
        """

        # The reason we have this code as a separate method is because we want
        # to isolate Prefect's async calls from Django's sync-restricted calls
        # (i.e. django raises errors if called within an async context).

        async with get_client() as client:
            response = await client.read_flow_runs(
                flow_run_filter=FlowRunFilter(
                    id={"any_": prefect_flow_run_ids},
                    state={"type": {"any_": ["SCHEDULED", "PENDING", "RUNNING"]}},
                ),
            )

        still_running_ids = [str(entry.id) for entry in response]

        return still_running_ids

    def update_flow_run_ids(self):
        """
        Queries Prefect to see how many workflows are in a scheduled, running,
        or pending state from the list of run ids that are associate with this
        structure source.
        """

        # make the async call to Prefect client
        still_running_ids = self._check_still_running_ids(self.prefect_flow_run_ids)

        # we now have our new list of IDs! Let's update it to the database
        self.prefect_flow_run_ids = still_running_ids
        self.save()

        return still_running_ids

    @property
    def nprefect_flow_runs(self):
        # update our ids before we report how many there are.
        runs = self.update_flow_run_ids()
        # now the currently running ones is just the length of ids!
        return len(runs)
