# -*- coding: utf-8 -*-

from simmate.database.base_data_types import table_column, DatabaseTable

from prefect import Client
from prefect.utilities.graphql import with_args


class EvolutionarySearch(DatabaseTable):

    # consider formula_full or chemical_system by making a composition-based mixin
    composition = table_column.CharField(max_length=50)

    # Import path for the workflow(s)
    individuals_datatable = table_column.CharField(max_length=200)

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

    class Meta:
        app_label = "local_calculations"


class StructureSource(DatabaseTable):

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
                            # "flow": {"name": {"_eq": self.search.workflow}},
                            "state": {"_in": ["Completed", "Scheduled"]},
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

    class Meta:
        app_label = "local_calculations"
