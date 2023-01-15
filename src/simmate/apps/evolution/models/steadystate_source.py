# -*- coding: utf-8 -*-

import logging

from rich import print

import simmate.toolkit.creators as creation_module
import simmate.toolkit.transformations as transform_module
import simmate.toolkit.transformations.from_ase as ase_transform_module
from simmate.database.base_data_types import DatabaseTable, table_column
from simmate.toolkit import Composition
from simmate.workflow_engine.execution import WorkItem


class SteadystateSource(DatabaseTable):
    class Meta:
        app_label = "workflows"

    name = table_column.CharField(max_length=50)
    kwargs = table_column.JSONField(default=dict)

    nsteadystate_target = table_column.FloatField(null=True, blank=True)

    is_creator = table_column.BooleanField()
    is_transformation = table_column.BooleanField()

    # This list limits to ids that are submitted or running
    workitem_ids = table_column.JSONField(default=list)

    search = table_column.ForeignKey(
        "FixedCompositionSearch",
        on_delete=table_column.CASCADE,
        related_name="steadystate_sources",
    )

    def update_flow_workitem_ids(self):
        """
        Queries Prefect to see how many workflows are in a scheduled, running,
        or pending state from the list of run ids that are associate with this
        structure source.
        """

        # Before updating our run ids, we first want to see if any of them
        # failed (or "E" for ERRORED) -- so that we can warn the use to
        # check their logs.
        failed_ids = WorkItem.objects.filter(
            id__in=self.workitem_ids,
            status__in=["E", "C"],
        ).values_list("id", flat=True)

        if failed_ids:
            logging.warning(
                f"The following WorkItem IDs failed or were cancelled: {list(failed_ids)}."
            )

            print("\n------------------------------------------------------------\n")
            print("Make sure you check your worker logs for more info.\n")
            print("You can preview ALL failed jobs in the command line:")
            print("simmate workflow-engine show-error-summary\n")
            print("Or view a specific error (w. full trackback) in python:")
            print("from simmate.workflow_engine.execution import WorkItem")
            print(f"item = WorkItem.objects.get(id={failed_ids[0]})")
            print("item.result()\n")
            print(
                "The call to `result()` will raise the error that caused your job "
                "to fail. Please report this error if you think it's a bug "
                "with Simmate.\n "
            )
            print(
                "Note, ~0-1% of calculations failing can be normal during an "
                "evolutionary search because generated structures may be "
                "unreasonable (and cause programs like VASP to crash). "
                "However, >1% can indicate a serious problem.\n"
            )
            print("------------------------------------------------------------\n")

        # check which ids are still running. Note, this is a separate
        # method in case it's an async call to Prefect client
        still_running_ids = self._check_still_running_ids(self.workitem_ids)

        # we now have our new list of IDs! Let's update it to the database
        self.workitem_ids = still_running_ids
        self.save()

        return still_running_ids

    @property
    def nflow_runs(self):
        # update our ids before we report how many there are.
        runs = self.update_flow_workitem_ids()
        # now the currently running ones is just the length of ids!
        return len(runs)

    @staticmethod
    def _check_still_running_ids(workitem_ids):
        """
        Queries Prefect to see check on a list of flow run ids and determines
        which ones are still in a scheduled, running, or pending state.
        From the list of ids given, it will return a list of the ones that
        haven't finished yet.
        This is normally used within `update_flow_workitem_ids` and shouldn't
        be called directly.
        """
        # The reason we have this code as a separate method is because we want
        # to allow isolation of Prefect's async calls from Django's
        # sync-restricted calls (i.e. django raises errors if called
        # within an async context).
        still_running_ids = WorkItem.objects.filter(
            id__in=workitem_ids,
            status__in=["P", "R"],
        ).values_list("id", flat=True)
        return list(still_running_ids)

    def to_toolkit(self):
        if self.is_transformation:
            return self._init_transformation()
        elif self.is_creator:
            return self._init_creator()

    def _init_transformation(self):

        if not self.is_transformation:
            raise Exception("This should not be called on non-transformations")

        # Consider moving to _deserialize_parameters. Only issue is that
        # I can't serialize these classes yet.
        if self.name.startswith("from_ase."):
            # all start with "from_ase" so I assume that import for now
            ase_class_str = self.name.split(".")[-1]
            transformation_class = getattr(ase_transform_module, ase_class_str)
            transformer = transformation_class(**self.kwargs)
        # !!! There aren't any common transformations that don't accept composition
        # as an input, but I expect this to change in the future.
        elif self.name in ["ExtremeSymmetry"]:
            transformation_class = getattr(transform_module, self.name)
            transformer = transformation_class(**self.kwargs)
        else:
            raise Exception(f"Transformation class {self.name} could not be found.")
        return transformer

    def _init_creator(self):

        if not self.is_creator:
            raise Exception("This should not be called on non-creators")

        composition = Composition(self.search.composition)

        # Consider moving to _deserialize_parameters. Only issue is that
        # I can't serialize these classes yet.
        try:
            creator_class = getattr(creation_module, self.name)
            creator = creator_class(composition, **self.kwargs)
        except:
            raise Exception(f"Creator class {self.name} could not be found.")
        return creator

    # This method is for Prefect 2.0
    # from simmate.utilities import async_to_sync
    # @staticmethod
    # @async_to_sync
    # async def _check_still_running_ids(workitem_ids):
    #     """
    #     Queries Prefect to see check on a list of flow run ids and determines
    #     which ones are still in a scheduled, running, or pending state.
    #     From the list of ids given, it will return a list of the ones that
    #     haven't finished yet.
    #     This is normally used within `update_flow_workitem_ids` and shouldn't
    #     be called directly.
    #     """
    #     raise NotImplementedError("porting to general executor")
    #     from prefect.client import get_client
    #     from prefect.orion.schemas.filters import FlowRunFilter
    #     # The reason we have this code as a separate method is because we want
    #     # to isolate Prefect's async calls from Django's sync-restricted calls
    #     # (i.e. django raises errors if called within an async context).
    #     async with get_client() as client:
    #         response = await client.read_flow_runs(
    #             flow_run_filter=FlowRunFilter(
    #                 id={"any_": workitem_ids},
    #                 state={"type": {"any_": ["SCHEDULED", "PENDING", "RUNNING"]}},
    #             ),
    #         )
    #     still_running_ids = [str(entry.id) for entry in response]
    #     return still_running_ids
