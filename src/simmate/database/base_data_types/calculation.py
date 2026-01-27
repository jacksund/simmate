# -*- coding: utf-8 -*-

import platform
from datetime import datetime

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
        "started_at",
        "finished_at",
    ]

    api_filters = {
        "workflow_name": ["exact"],
        "workflow_version": ["exact"],
        "computer_system": ["exact"],
        "directory": ["exact"],
        "run_id": ["exact"],
        "total_time": ["range"],
        "queue_time": ["range"],
    }

    started_at = table_column.DateTimeField(blank=True, null=True)
    """
    Timestamp of when the calculation starting running
    """

    finished_at = table_column.DateTimeField(blank=True, null=True)
    """
    Timestamp of when the calculation completed
    """

    total_time = table_column.FloatField(blank=True, null=True)
    """
    The total calculation time in seconds. Equal to the finished_at minus
    started_at column.
    """

    queue_time = table_column.FloatField(blank=True, null=True)
    """
    The total time the calculation was waiting in the queue in seconds. Equal 
    to the started_at column minus created_at.
    """

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

    run_id = table_column.UUIDField(blank=True, null=True, unique=True)
    """
    The run id (UUID) for this calculation. Note, this is not a foreign key to
    the WorkItem model because that model is only used on cloud-based submissions.
    Local runs and subworkflows still get a run_id, but it will not have a
    corresponding WorkItem.

    An example id is... d8a785e1-e344-463a-bede-0e7b3da7bab6
    """

    status_options = [
        "Pending",
        "Running",
        "Canceled",
        "Failed",
        "Completed",
    ]
    status = table_column.CharField(
        max_length=10,
        blank=True,
        null=True,
    )
    """
    The status/state of the calculation
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
        run_id: str = None,
        workflow_name: str = None,
        workflow_version: str = None,
        started_at: datetime = None,
        finished_at: datetime = None,
        status: str = None,
        **kwargs,  # other parameters you'd normally pass to 'from_toolkit'
    ):
        """
        Given a run id, this method will do one of the following...

        1. if it exists, load the database object with matching run_id
        2. if it doesn't exist, create a new database object using this ID and extra kwargs

        It will then return the corresponding Calculation instance.
        """

        # Depending on how a workflow was submitted, there may be a calculation
        # extry existing already -- which we need to grab and then update. If it's
        # not there, we create a new one

        # check if the calculation already exists in our database, and if not,
        # we need to create a new one
        if not cls.objects.filter(run_id=run_id).exists():
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
        # Otherwise the entry exists and we can load it
        else:
            calculation = cls.objects.get(run_id=run_id)

        # if this is the start of a calculation run (and not just scheduling via
        # run cloud) then we also want to add a timestamp for the start
        if started_at:
            calculation.started_at = started_at
            queue_time = (
                calculation.started_at - calculation.created_at
            ).total_seconds()
            # if we run the workflow locally, this can sometimes give a negative
            # value for queue time because of database hit / python continutation
            # inconsistencies. We therefore give a minimum value of 0
            if queue_time < 0:
                queue_time = 0
            calculation.queue_time = queue_time
            calculation.save()

        if finished_at:
            calculation.finished_at = finished_at
            calculation.total_time = (
                calculation.finished_at - calculation.started_at
            ).total_seconds()
            calculation.save()

        if status and calculation.status != status:
            calculation.status = status
            calculation.save()

        return calculation
