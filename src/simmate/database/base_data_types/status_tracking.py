# -*- coding: utf-8 -*-

import plotly.express as plotly_express
from django.utils import timezone
from pandas import DataFrame
from simple_history.models import HistoricalRecords

from .base import DatabaseTable, table_column


class StatusTracking(DatabaseTable):
    """
    A calculation is the result of a single `workflow.run()` call. Thus, a
    calculation is synonmyous with a Prefect "Flow-Run". Becuase of this,
    every table that inherits from this Calculation class will be directly
    linked to a specific Workflow. You can access this workflow via the
    `workflow` attribute.
    """

    class Meta:
        abstract = True

    # -------------------------------------------------------------------------

    # NOTE: many child classes override these defaults

    status_choices = [
        "Under Review",
        "In Progress",
        "On Hold",
        "Completed",
        "Canceled",
        "Failed",
        "Staged for Deletion",
    ]
    status = table_column.CharField(
        max_length=50,
        null=True,
        blank=True,
    )
    """
    The current status of the entry/request.
    
    Possible values:
        - "Under Review": Request is currently being evaluated.
        - "In Progress": Work on the request has started.
        - "On Hold": Request is paused or awaiting additional input.
        - "Completed": Request has been fulfilled successfully.
        - "Canceled": Request was stopped before completion.
        - "Failed": Request could not be completed due to an error or issue.
        - "Staged for Deletion": Request is marked for removal from the database.
    """

    # BUG: must be set by child class
    # history = HistoricalRecords()

    # -------------------------------------------------------------------------

    status_completed_name: str = "Completed"
    """
    Name of the status to be used for calculating `days_to_completed`. By
    default this is `Completed` but some apps use an alternative status such
    as `Synthesized`, `Registered`, `Fixed`, etc.
    """

    days_to_completed = table_column.IntegerField(null=True, blank=True)
    """
    The total number of days it took for the target to go from initial
    submission (`created_at`) to reaching a status of synthesized/completed state.
    """

    def get_days_to_completed(self) -> int:
        # TODO: consider doing from "In Progress" to "Completed", instead of
        # "created_at" to "Completed"
        return (
            int(
                self.get_status_timedelta(self.status_completed_name).total_seconds()
                / 60
                / 60
                / 24
            )
            if self.status == self.status_completed_name
            else None
        )

    @classmethod
    def update_days_to_completed(cls):
        for target in cls.objects.filter(
            status=cls.status_completed_name,
            days_to_completed__isnull=True,
        ).all():
            num_days = target.get_days_to_completed()
            if num_days:
                target.update_wo_timestamp(days_to_completed=num_days)

    # -------------------------------------------------------------------------

    status_age_enable = ["Proposed", "In Progress", "Contracted (CRO)"]
    status_age_disable = [
        "Reference Only",
        "Proposal Rejected",
        "Synthesized",
        "Synthesis Failed",
        "Staged for Deletion",
    ]

    status_age = table_column.IntegerField(null=True, blank=True)
    """
    The total number of days that the entry has been sitting with its current
    status.

    Note, this is only tracked for pending status types (see `status_age_enable` list). 
    Once synthesized/canceled/etc, this will revert to None (see `status_age_disable` list)
    """

    def get_status_age(self) -> int:
        """
        Gives the age of the current status in days
        """
        current_date = timezone.now()
        status_start_date = self.get_status_timestamp(self.status)
        return int((current_date - status_start_date).total_seconds() / 60 / 60 / 24)

    @classmethod
    def update_status_age(cls):
        """
        Updates the status age column for all entries in the table
        """

        # unset any `status_age` set for columns that should no longer have them
        for target in cls.objects.filter(
            status__in=cls.status_age_disable,
            status_age__isnull=False,
        ).all():
            target.update_wo_timestamp(status_age=None)

        # update `status_age`
        for target in cls.objects.filter(
            status__in=cls.status_age_enable,
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

    enable_html_report = False  # disabled by default
    report_df_columns = [
        "created_at",
        "status",
        "days_to_completed",
        "status_age",
    ]
    status_color_map = {
        "Under Review": "rgba(249, 200, 81, 1)",  # yellow
        "In Progress": "rgba(4, 144, 204, 1)",  # blue
        "On Hold": "rgba(0, 0, 0, 1)",  # black
        "Completed": "rgba(16, 196, 105, 1)",  # green
        "Canceled": "rgba(200, 200, 200, 1)",  # light grey
        "Failed": "rgba(255, 91, 91, 1)",  # red
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
        df_s = df[df.status.isin(cls.status_age_enable)]
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
