# -*- coding: utf-8 -*-

import platform

from simmate.database.base_data_types import DatabaseTable, table_column


class Calculation(DatabaseTable):
    """
    A calculation is the result of a single `workflow.run()` call. Thus, a
    calculation is synonmyous with a Prefect "Flow-Run". Becuase of this,
    every table that inherits from this Calculation class will be directly
    linked to a specific Workflow. You can access this workflow via the
    `workflow` attribute.
    """

    class Meta:
        abstract = True
        app_label = "workflows"

    archive_fields = [
        "workflow_name",
        "workflow_version",
        "computer_system",
        "directory",
        "run_id",
        "corrections",
    ]

    api_filters = {
        "workflow_name": ["exact"],
        "workflow_version": ["exact"],
        "computer_system": ["exact"],
        "directory": ["exact"],
        "run_id": ["exact"],
    }

    workflow_name = table_column.CharField(
        max_length=75,
        blank=True,
        null=True,
    )
    """
    The full name of the workflow used, such as "relaxation.vasp.matproj".
    """

    workflow_version = table_column.CharField(
        max_length=75,
        blank=True,
        null=True,
    )
    """
    The version of the workflow being used, such as "0.7.0".
    """

    computer_system = table_column.CharField(
        max_length=75,
        blank=True,
        null=True,
    )
    """
    This is the location/computer that the workflow was ran on. It will be something
    like... "DESKTOP-PVN50G5" or "Warwulf". This value is set automatically
    using `platform.node()`
    """

    directory = table_column.CharField(
        max_length=250,
        blank=True,
        null=True,
    )
    """
    This is the folder that the workflow was ran in. It will be something
    like... "/path/to/simmate-task-abc123"
    """

    run_id = table_column.CharField(
        max_length=50,
        blank=True,
        null=True,
        unique=True,
    )
    """
    If this was submitted through Prefect, there is a lot more metadata available
    for this calculation. Simmate does not store this data directly, but instead
    we store the flow-run-id so that the user may look this up in the Prefect
    database if they wish.
    An example id is... d8a785e1-e344-463a-bede-0e7b3da7bab6
    """

    corrections = table_column.JSONField(blank=True, null=True)
    """
    S3 workflows often have ErrorHandlers that fix any issues while the
    calaculation ran. This often involves changing settings, so we store
    any of those changes here.
    """

    @classmethod
    def from_run_context(
        cls,
        run_id: str,
        workflow_name: str = None,
        workflow_version: str = None,
        **kwargs,  # other parameters you'd normally pass to 'from_toolkit'
    ):
        """
        Given a prefect id, this method will do one of the following...

        1. if it exists, load the database object with matching prefect_id
        2. if it doesn't exist, create a new database object using this ID and extra kwargs

        It will then return the corresponding Calculation instance.
        """

        # Depending on how a workflow was submitted, there may be a calculation
        # extry existing already -- which we need to grab and then update. If it's
        # not there, we create a new one

        # check if the calculation already exists in our database, and if so,
        # grab it and return it.
        if cls.objects.filter(run_id=run_id).exists():
            return cls.objects.get(run_id=run_id)
        # Otherwise we need to create a new one and return that.

        # To handle the initialization of other Simmate mix-ins, we pass all
        # information to the from_toolkit method rather than directly to cls.
        calculation = cls.from_toolkit(
            run_id=run_id,
            computer_system=platform.node(),
            workflow_name=workflow_name,
            workflow_version=workflow_version,
            **kwargs,
        )
        calculation.save()

        return calculation

    # -------------------------------------------------------------------------
    # All methods below are for prefect, but because of the prefect 2.0 migration,
    # these are disabled for the time being.
    # -------------------------------------------------------------------------

    # @classmethod
    # def from_run_context(
    #     cls,
    #     run_id: str = None,  # inputs are optional when using prefect
    #     workflow_name: str = None,
    #     **kwargs,  # other parameters you'd normally pass to 'from_toolkit'
    # ):
    #     if not run_id or not workflow_name:
    #         # Grab the database_table that we want to save the results in
    #         from prefect.context import FlowRunContext
    #         run_context = FlowRunContext.get()
    #         if run_context:
    #             workflow = run_context.flow.simmate_workflow
    #             workflow_name = workflow.name_full
    #             run_id = str(run_context.flow_run.id)
    #             assert workflow.database_table == cls
    #         else:
    #             raise Exception(
    #                 "No Prefect FlowRunContext was detected, so you must provide "
    #                 "flow_id and workflow_name to the from_run_context method."
    #             )

    # @property
    # def prefect_cloud_link(self) -> str:
    #     """
    #     URL to this calculation (flow-run) in the Prefect Cloud website.
    #     This assumes that the calculation was registered with prefect cloud and
    #     doesn't check to confirm it's been registered. To actually confirm that,
    #     use the `flow_run_view` attribute instead.
    #     """
    #     return f"https://cloud.prefect.io/simmate/flow-run/{self.run_id}"

    # @property
    # def flow_run_view(self):  # -> FlowRunView
    #     """
    #     Checks if the run_id was registered with Prefect Cloud, and
    #     if so, returns a
    #     [FlowRunView](https://docs.prefect.io/orchestration/flow-runs/inspection.html)
    #     that hold metadata such as the status. This metadata includes...
    #         - agent_id
    #         - auto_scheduled
    #         - context
    #         - created_by_user_id
    #         - end_time
    #         - flow_id
    #         - labels
    #         - name
    #         - parameters
    #         - scheduled_start_time
    #         - start_time
    #         - state
    #         - tenant_id
    #         - times_resurrected
    #         - version
    #     If Prefect Cloud is not configured or if the calculation was ran
    #     locally, the None is returned.
    #     """
    #     raise NotImplementedError("This feature has no been migrated to Prefect 2.0")

    # @property
    # def prefect_flow_run_name(self) -> str:
    #     """
    #     Gives the user-friendly name of this run if the run_id
    #     was registered with Prefect Cloud. (an example name is "friendly-bumblebee").
    #     """
    #     flowrunview = self.flow_run_view
    #     return flowrunview.name if flowrunview else None

    # @property
    # def prefect_state(self) -> str:
    #     """
    #     Gives the current state of this run if the run_id
    #     was registered with Prefect Cloud. (ex: "Scheduled" or "Successful")
    #     """
    #     flowrunview = self.flow_run_view
    #     return flowrunview.state.__class__.__name__ if flowrunview else None
