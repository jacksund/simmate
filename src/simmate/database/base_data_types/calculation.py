# -*- coding: utf-8 -*-

# from prefect.backend.flow_run import FlowRunView

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

    base_info = [
        "directory",
        "prefect_flow_run_id",
        "created_at",
        "updated_at",
        "corrections",
    ]

    directory = table_column.CharField(
        max_length=250,
        blank=True,
        null=True,
    )
    """
    This is the folder that the workflow was ran in. It will be something
    like... "/path/to/simmate-task-abc123"
    """
    # TODO: maybe add host computer name too? (via platform.node())

    prefect_flow_run_id = table_column.CharField(
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
    Simmate workflows often have ErrorHandlers that fix any issues while the
    calaculation ran. This often involves changing settings, so we store
    any of those changes here.
    """

    @property
    def prefect_cloud_link(self) -> str:
        """
        URL to this calculation (flow-run) in the Prefect Cloud website.

        This assumes that the calculation was registered with prefect cloud and
        doesn't check to confirm it's been registered. To actually confirm that,
        use the `flow_run_view` attribute instead.
        """
        return f"https://cloud.prefect.io/simmate/flow-run/{self.prefect_flow_run_id}"

    @property
    def flow_run_view(self):  # -> FlowRunView
        """
        Checks if the prefect_flow_run_id was registered with Prefect Cloud, and
        if so, returns a
        [FlowRunView](https://docs.prefect.io/orchestration/flow-runs/inspection.html)
        that hold metadata such as the status. This metadata includes...
            - agent_id
            - auto_scheduled
            - context
            - created_by_user_id
            - end_time
            - flow_id
            - labels
            - name
            - parameters
            - scheduled_start_time
            - start_time
            - state
            - tenant_id
            - times_resurrected
            - version

        If Prefect Cloud is not configured or if the calculation was ran
        locally, the None is returned.
        """
        raise NotImplementedError("Migrating to Prefect 2.0")
        try:
            return FlowRunView.from_flow_run_id(self.prefect_flow_run_id)
        except:  # may fail if this is a local run or prefect api key not configured
            return None

    @property
    def prefect_flow_run_name(self) -> str:
        """
        Gives the user-friendly name of this run if the prefect_flow_run_id
        was registered with Prefect Cloud. (an example name is "friendly-bumblebee").
        """
        flowrunview = self.flow_run_view
        return flowrunview.name if flowrunview else None

    @property
    def prefect_state(self) -> str:
        """
        Gives the current state of this run if the prefect_flow_run_id
        was registered with Prefect Cloud. (ex: "Scheduled" or "Successful")
        """
        flowrunview = self.flow_run_view
        return flowrunview.state.__class__.__name__ if flowrunview else None

    @classmethod
    def from_prefect_id(cls, prefect_flow_run_id: str, **kwargs):
        """
        Given a prefect id, this method will do one of the following...

        1. if it exists, load the database object with matching prefect_id
        2. if it doesn't exist, create a new database object using this ID and extra kwargs

        It will then return the corresponding Calculation instance.
        """

        # Depending on how a workflow was submitted, there may be a calculation
        # extry existing already -- which we need to grab and then update. If it's
        # not there, we create a new one!

        # check if the calculation already exists in our database, and if so,
        # grab it and return it.
        if cls.objects.filter(prefect_flow_run_id=prefect_flow_run_id).exists():
            return cls.objects.get(prefect_flow_run_id=prefect_flow_run_id)
        # Otherwise we need to create a new one and return that.

        # To handle the initialization of other Simmate mix-ins, we pass all
        # information to the from_toolkit method rather than directly to cls.
        calculation = cls.from_toolkit(
            prefect_flow_run_id=prefect_flow_run_id,
            **kwargs,
        )
        calculation.save()

        return calculation

    # TODO: Consider adding resource use metadata (e.g. from VASP)
    # I may want to add these fields because Prefect doesn't store run stats
    # indefinitely AND it doesn't give detail memory use, number of cores, etc.
    # If all of these are too much, I could do a json field of "run_stats" instead
    #   - average_memory (The average memory used in kb)
    #   - max_memory (The maximum memory used in kb)
    #   - elapsed_time (The real time elapsed in seconds)
    #   - system_time(The system CPU time in seconds)
    #   - user_time(The user CPU time spent by VASP in seconds)
    #   - total_time (The total CPU time for this calculation)
    #   - cores (The number of cores used by VASP (some clusters print `mpi-ranks` here))

    # TODO: Consider linking to parent calculations for nested workflow runs
    # Where this calculation plays a role within a "nested" workflow calculation.
    # Becuase this structure can be reused by multiple workflows, we make this
    # a list of source-like objects. For example, a relaxation could be part of
    # a series of relaxations (like in StagedRelaxation) or it can be an initial
    # step of a BandStructure calculation.
    # parent_nested_calculations = table_column.JSONField(blank=True, null=True)
