# -*- coding: utf-8 -*-

from simmate.database.base_data_types import table_column, DatabaseTable

from django.apps import apps as django_apps

from prefect import Client
from prefect.utilities.graphql import with_args

from plotly.subplots import make_subplots
import plotly.graph_objects as plotly_go


class EvolutionarySearch(DatabaseTable):
    class Meta:
        app_label = "local_calculations"

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
            app_label="local_calculations",
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

    @property
    def best_individual(self):
        best = self.individuals_completed.order_by("energy_per_atom").first()
        return best

    def get_convergence_plot(self):

        # Grab the calculation's structure and convert it to a dataframe
        structures_dataframe = self.structures.order_by(
            "ionic_step_number"
        ).to_dataframe()

        # We will be making a figure that consists of 3 stacked subplots that
        # all share the x-axis of ionic_step_number
        figure = make_subplots(
            rows=3,
            cols=1,
            shared_xaxes=True,
        )

        # Generate a plot for Energy (per atom)
        figure.add_trace(
            plotly_go.Scatter(
                x=structures_dataframe["ionic_step_number"],
                y=structures_dataframe["energy_per_atom"],
            ),
            row=1,
            col=1,
        )

        # Generate a plot for Forces (norm per atom)
        figure.add_trace(
            plotly_go.Scatter(
                x=structures_dataframe["ionic_step_number"],
                y=structures_dataframe["site_forces_norm_per_atom"],
            ),
            row=2,
            col=1,
        )

        # Generate a plot for Stress (norm per atom)
        figure.add_trace(
            plotly_go.Scatter(
                x=structures_dataframe["ionic_step_number"],
                y=structures_dataframe["lattice_stress_norm_per_atom"],
            ),
            row=3,
            col=1,
        )

        # Now let's clean up some formatting and add the axes titles
        figure.update_layout(
            width=600,
            height=600,
            showlegend=False,
            xaxis3_title="Ionic Step (#)",
            yaxis_title="Energy (eV/atom)",
            yaxis2_title="Site Forces",
            yaxis3_title="Lattice Stress",
        )

        # we return the figure object for the user
        return figure

    def view_convergence_plot(self):
        import plotly.io as pio

        pio.renderers.default = "browser"

        figure = self.get_convergence_plot()
        figure.show()


class StructureSource(DatabaseTable):
    class Meta:
        app_label = "local_calculations"

    name = table_column.CharField(max_length=50)

    is_steadystate = table_column.BooleanField()
    is_singleshot = table_column.BooleanField()

    settings = table_column.JSONField(default={})

    # timestamping for when this was added to the database
    # This also gives a feel for how long the steady-state was running
    created_at = table_column.DateTimeField(auto_now_add=True)
    updated_at = table_column.DateTimeField(auto_now=True)

    # This list limits to ids that are submitted or running
    prefect_flow_run_ids = table_column.JSONField(default=[])

    search = table_column.ForeignKey(
        EvolutionarySearch,
        on_delete=table_column.CASCADE,
        related_name="sources",
    )

    def update_flow_run_ids(self):

        # Using our list of current run ids, we query prefect to see which of
        # these still are running or in the queue.
        # OPTIMIZE: This may be a really bad way to query Prefect...
        query = {
            "query": {
                with_args(
                    "flow_run",
                    {
                        "where": {
                            "state": {"_in": ["Running", "Scheduled"]},
                            "id": {"_in": self.prefect_flow_run_ids},
                        },
                    },
                ): ["id"]
            }
        }
        client = Client()
        result = client.graphql(query)
        # graphql gives a weird format, so I reparse it into just a list of ids
        result = [run["id"] for run in result["data"]["flow_run"]]

        # we now have our new list of IDs! Let's update it to the database
        self.prefect_flow_run_ids = result
        self.save()

        # in case we need the list of ids, we return it too
        return result

    @property
    def nprefect_flow_runs(self):
        # update our ids before we report how many there are.
        runs = self.update_flow_run_ids()
        # now the currently running ones is just the length of ids!
        return len(runs)
