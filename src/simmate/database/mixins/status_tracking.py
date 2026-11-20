import plotly.express as plotly_express
from django.utils import timezone
from pandas import DataFrame

from ..core import DatabaseTable, table_column


class StatusTracking(DatabaseTable):
    """
    Adds a `status` column for request-like entries (e.g. inventory requests),
    along with how long each entry has sat in its current status
    (`status_age`) and how long it took to complete (`days_to_completed`).

    Child tables must add a `history` table (via django-simple-history), which
    is where the timestamp of each status change comes from (see the note on
    `history` below). The cached `status_age` and `days_to_completed` columns
    are refreshed with `update_status_age` and `update_days_to_completed`
    (e.g. in a daily schedule).
    """

    class Meta:
        abstract = True

    # -------------------------------------------------------------------------

    # NOTE: child classes can override these defaults

    status_options = [
        "Under Review",
        "Approved",
        "In Progress",
        "On Hold",
        "Completed",
        "Failed",
        "Rejected",
        "Canceled",
        "Duplicate",
        "Staged for Deletion",
    ]
    status = table_column.CharField(
        max_length=50,
        null=True,
        blank=True,
    )
    """
    The current status of the entry. Must be one of `status_options`.

    Possible values:
        - "Under Review": submitted and waiting for a decision.
        - "Approved": accepted and queued, but work has not started.
        - "In Progress": work has started (e.g. synthesis is underway or an
          order was placed).
        - "On Hold": paused or waiting on more input.
        - "Completed": fulfilled successfully.
        - "Failed": attempted, but could not be completed.
        - "Rejected": declined by a reviewer.
        - "Canceled": withdrawn before completion (e.g. by the requester).
        - "Duplicate": closed because another entry covers it.
        - "Staged for Deletion": marked for removal from the database.
    """

    open_status_options = [
        "Under Review",
        "Approved",
        "In Progress",
        "On Hold",
    ]
    """
    The statuses where an entry is still pending. Only these have a
    `status_age`.
    """

    # NOTE: `history` must be set by each child class. It isn't set here with
    # `HistoricalRecords(inherit=True)` because inherited history tables
    # can't be given a `table_name`, and we want them to follow the naming of
    # other simmate tables. For example:
    #   from simple_history.models import HistoricalRecords
    #   history = HistoricalRecords(table_name="example__requests__history")

    # -------------------------------------------------------------------------

    status_completed_name: str = "Completed"
    """
    Name of the status to be used for calculating `days_to_completed`. By
    default this is `Completed`, but child classes can use an alternative
    status (e.g. `Synthesized` or `Fixed`).
    """

    days_to_completed = table_column.IntegerField(null=True, blank=True)
    """
    The total number of days it took for the entry to go from initial
    submission (`created_at`) to reaching the `status_completed_name` status.
    """

    def get_days_to_completed(self) -> int:
        # TODO: consider doing from "In Progress" to "Completed", instead of
        # "created_at" to "Completed"
        if self.status != self.status_completed_name:
            return None
        timedelta = self.get_status_timedelta(self.status_completed_name)
        if timedelta is None:
            return None
        return int(timedelta.total_seconds() / 60 / 60 / 24)

    @classmethod
    def update_days_to_completed(cls):
        for target in cls.objects.filter(
            status=cls.status_completed_name,
            days_to_completed__isnull=True,
        ).all():
            num_days = target.get_days_to_completed()
            if num_days is not None:
                target.update_wo_timestamp(days_to_completed=num_days)

    # -------------------------------------------------------------------------

    status_age = table_column.IntegerField(null=True, blank=True)
    """
    The total number of days that the entry has been sitting with its current
    status.

    Note, this is only tracked for pending statuses (see `open_status_options`).
    Once the entry is completed, canceled, etc., this reverts to None.
    """

    def get_status_age(self) -> int:
        """
        Gives the age of the current status in days
        """
        current_date = timezone.now()
        status_start_date = self.get_status_timestamp(self.status)
        if status_start_date is None:
            return None
        return int((current_date - status_start_date).total_seconds() / 60 / 60 / 24)

    @classmethod
    def update_status_age(cls):
        """
        Updates the status age column for all entries in the table
        """

        # unset any `status_age` for entries that are no longer pending
        cls.objects.exclude(status__in=cls.open_status_options).filter(
            status_age__isnull=False
        ).update(status_age=None)

        # update `status_age`
        for target in cls.objects.filter(
            status__in=cls.open_status_options,
        ).all():
            target.update_wo_timestamp(status_age=target.get_status_age())

    # -------------------------------------------------------------------------

    def get_status_timestamp(self, status: str):  # -> returns datetime
        """
        Grabs the timestamp of when a status first occurred in the entry history.
        """

        # BUG: logic bug where someone might set status incorrectly and have
        # it later switch back.
        # Ex: I submitted an entry under status Complete --> switched it back
        # to In Progress --> months later marked it as Complete.
        # The 2nd Complete is actually what we want here!
        # We assume the 1st occurence is the legit one here.

        # grab the first historical instance where it changed to this status
        historic_obj = (
            self.history.filter(status=status).order_by("history_date").first()
        )

        # if there is no instance, then we cant get a timestamp
        return historic_obj.updated_at if historic_obj else None

    def get_status_timedelta(self, status: str):  # -> returns timedelta
        """
        Grabs the time it took for the entry to reach a given status, relative
        to when the entry was first submitted
        """

        # grab the first historical instance where it changed to this status
        status_timestamp = self.get_status_timestamp(status=status)

        if status_timestamp:
            # difference between when the obj was first created and now
            time_to_status = status_timestamp - self.created_at
            return time_to_status

    # -------------------------------------------------------------------------

    enable_report = False  # disabled by default
    report_df_columns = [
        "created_at",
        "status",
        "days_to_completed",
        "status_age",
    ]
    status_color_map = {
        "Under Review": "rgba(249, 200, 81, 1)",  # yellow
        "Approved": "rgba(120, 200, 235, 1)",  # light blue
        "In Progress": "rgba(4, 144, 204, 1)",  # blue
        "On Hold": "rgba(0, 0, 0, 1)",  # black
        "Completed": "rgba(16, 196, 105, 1)",  # green
        "Failed": "rgba(255, 91, 91, 1)",  # red
        "Rejected": "rgba(253, 126, 20, 1)",  # orange
        "Canceled": "rgba(200, 200, 200, 1)",  # light grey
        "Duplicate": "rgba(200, 200, 200, 1)",  # light grey
        "Staged for Deletion": "rgba(100, 100, 100, 1)",  # dark grey
    }

    @classmethod
    def get_status_tracking_report_from_df(cls, df: DataFrame):
        return {
            "status_pie_chart": cls.get_status_pie_chart(df),
            "created_at_histogram": cls.get_created_at_histogram(df),
            "age_histogram": cls.get_age_histogram(df),
            "days_to_completed_histogram": cls.get_days_to_completed_histogram(df),
        }

    @classmethod
    def get_status_pie_chart(cls, df: DataFrame):
        status_counts = df["status"].value_counts().reset_index()
        status_counts.columns = ["status", "count"]
        figure = plotly_express.pie(
            status_counts,
            values="count",
            names="status",
            color="status",
            color_discrete_map=cls.status_color_map,
            hole=0.5,  # for a donut-like pie chart
        )
        return figure

    @classmethod
    def get_created_at_histogram(cls, df: DataFrame):
        # Plot a histogram of ages, grouped and colored by status
        figure = plotly_express.histogram(
            df,
            x="created_at",
            color="status",
            color_discrete_map=cls.status_color_map,
            labels={"created_at": ""},
        )
        figure.update_layout(
            yaxis_title="Count (#)",
            height=200,
        )
        return figure

    @classmethod
    def get_age_histogram(cls, df: DataFrame):
        df_s = df[df.status.isin(cls.open_status_options)]
        figure = plotly_express.histogram(
            df_s,
            x="status_age",
            color="status",
            color_discrete_map=cls.status_color_map,
            labels={"status_age": "Time in current status (days)"},
        )
        figure.update_layout(
            yaxis_title="Count (#)",
            height=200,
        )
        return figure

    @classmethod
    def get_days_to_completed_histogram(cls, df: DataFrame):
        df_s = df[df.status == cls.status_completed_name]
        figure = plotly_express.histogram(
            data_frame=df_s,
            x="days_to_completed",
            color="status",
            color_discrete_map=cls.status_color_map,
            labels={
                "days_to_completed": f"Submission to {cls.status_completed_name} Time (days)"
            },
        )
        figure.update_layout(
            yaxis_title="Count (#)",
            height=200,
        )
        return figure
