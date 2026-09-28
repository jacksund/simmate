# -*- coding: utf-8 -*-

from datetime import datetime

import pandas
import plotly.express as plotly_express
import plotly.graph_objects as plotly_go
from django.utils import timezone

from simmate.compute import WorkItem
from simmate.website.data_explorer.components import TableComponent

STATUS_LABELS = dict(WorkItem.StatusOptions.choices)

TIMELINE_COLORS = {
    "Pending": "#adb5bd",
    "Running": "#0d6efd",
    "Cancelled": "#fd7e14",
    "Errored": "#dc3545",
    "Finished": "#009485",
    "Submitted": "#6c757d",
    "Started": "#0dcaf0",
    "Queue wait": "#adb5bd",
    "Run time": "#0d6efd",
}


class WorkItemComponent(TableComponent):
    table = WorkItem
    display_name = "Work Items"
    description_short = (
        "Specific tasks or jobs that have been submitted to a queue for "
        "execution by workers. This table tracks the lifecycle of a "
        "calculation, including its parameters, status, and any errors "
        "encountered."
    )
    template_names = {
        "entries": "compute_management/work_items/table.html",
    }

    enable_report = True

    # NOTE: listing columns also keeps the pickled binary columns out of the
    # report query
    report_df_columns = [
        "id",
        "status",
        "tags",
        "created_at",
        "started_at",
        "updated_at",
        "worker_id",
        "worker__computer_system",
    ]

    report_views = ["activity", "queue_depth", "jobs", "durations"]

    # -------------------------------------------------------------------------
    # Report (shared by the data explorer and the compute dashboard)
    # -------------------------------------------------------------------------

    @classmethod
    def get_report_from_df(
        cls,
        df: pandas.DataFrame,
        start: datetime = None,
        end: datetime = None,
        views: list[str] = None,
    ) -> dict:
        """
        Builds timeline figures for a set of WorkItems.

        Args:
            df: WorkItems with (at least) the `report_df_columns`.
            start: The start of the time window to plot. Defaults to the
                earliest submission in `df`.
            end: The end of the time window. Defaults to now.
            views: Which figures to build (see `report_views`). Defaults to all.

        Returns:
            A dictionary mapping each view to a plotly figure, or None if there
            is no data for that view.
        """
        if df.empty:
            return {}

        df = cls.prepare_report_df(df)
        start = cls._to_local(start) if start else df["created_at"].min()
        end = cls._to_local(end) if end else cls._to_local(timezone.now())

        builders = {
            "activity": cls.get_activity_figure,
            "queue_depth": cls.get_queue_depth_figure,
            "jobs": cls.get_jobs_figure,
            "durations": cls.get_durations_figure,
        }
        return {
            view: builders[view](df, start, end) for view in views or cls.report_views
        }

    @staticmethod
    def _to_local(value):
        """
        Converts a datetime (or Series of them) to naive local time, which is
        what plotly displays as-is.
        """
        local_tz = str(timezone.get_current_timezone())
        if isinstance(value, pandas.Series):
            value = pandas.to_datetime(value, utc=True)
            return value.dt.tz_convert(local_tz).dt.tz_localize(None)
        value = pandas.Timestamp(value)
        value = value.tz_localize("UTC") if value.tzinfo is None else value
        return value.tz_convert(local_tz).tz_localize(None)

    @classmethod
    def prepare_report_df(cls, df: pandas.DataFrame) -> pandas.DataFrame:
        """
        Adds the derived columns used by the report figures: local timestamps,
        workflow name, status label, row label, and a start/end for every item.
        """
        df = df.rename(columns={"worker__computer_system": "host"}).copy()
        for column in ["created_at", "started_at", "updated_at"]:
            df[column] = cls._to_local(df[column])
        now = cls._to_local(timezone.now())

        df["workflow"] = df["tags"].apply(WorkItem.get_workflow_name)
        df["status_label"] = df["status"].map(STATUS_LABELS)
        df["short_id"] = df["id"].astype(str).str[:8]

        # finished/errored/cancelled items end at their last update. Everything
        # else is still ongoing.
        is_done = df["status"].isin(["F", "E", "C"])
        df["ended_at"] = df["updated_at"].where(is_done, now)

        # Items from before `started_at` existed: running items were started
        # at `updated_at`, but for finished ones the start is unknown.
        df["started_at"] = df["started_at"].fillna(
            df["updated_at"].where(df["status"] == "R")
        )

        def row_label(row) -> str:
            if row["status"] == "P":
                return "(queue)"
            elif pandas.notna(row["worker_id"]):
                host = row["host"] if pandas.notna(row["host"]) else "unknown host"
                return f"{host} · #{int(row['worker_id'])}"
            # API workers don't have a worker entry
            return "(no worker)"

        df["row_label"] = df.apply(row_label, axis=1)
        return df

    @staticmethod
    def _get_frequency(start, end) -> str:
        span = end - start
        if span <= pandas.Timedelta(days=2):
            return "1h"
        elif span <= pandas.Timedelta(days=14):
            return "6h"
        elif span <= pandas.Timedelta(days=90):
            return "1D"
        return "7D"

    @staticmethod
    def _style_figure(figure, height: int):
        # semi-transparent grid & neutral font so figures work in light/dark mode
        grid_color = "rgba(128,128,128,0.2)"
        figure.update_layout(
            height=height,
            margin=dict(t=30, r=15, l=50, b=35),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", x=0, y=1.02, yanchor="bottom", title=None),
            font=dict(size=12, color="#888888"),
            xaxis=dict(gridcolor=grid_color),
            yaxis=dict(gridcolor=grid_color),
        )
        return figure

    @classmethod
    def get_activity_figure(cls, df: pandas.DataFrame, start, end):
        """
        Stacked bars of items finishing, erroring, or being cancelled in each
        time bin, with lines for items submitted and started.
        """
        freq = cls._get_frequency(start, end)
        bins = pandas.date_range(start.floor(freq), end, freq=freq)
        bin_width = pandas.Timedelta(freq)

        def count_per_bin(times: pandas.Series) -> pandas.Series:
            times = times.dropna()
            times = times[times >= bins[0]]
            counts = times.dt.floor(freq).value_counts()
            return counts.reindex(bins, fill_value=0)

        figure = plotly_go.Figure()
        for status in ["F", "E", "C"]:
            label = STATUS_LABELS[status]
            counts = count_per_bin(df.loc[df["status"] == status, "ended_at"])
            figure.add_bar(
                x=bins + bin_width / 2,  # center bars within their bin
                y=counts.values,
                width=bin_width.total_seconds() * 1000 * 0.85,
                name=label,
                marker_color=TIMELINE_COLORS[label],
            )
        for label, column in [("Submitted", "created_at"), ("Started", "started_at")]:
            counts = count_per_bin(df[column])
            figure.add_scatter(
                x=bins + bin_width / 2,
                y=counts.values,
                name=label,
                mode="lines",
                line=dict(color=TIMELINE_COLORS[label], width=2, dash="dot"),
            )
        figure.update_layout(
            barmode="stack",
            hovermode="x unified",
            xaxis_range=[start, end],
            yaxis_title=f"Items per {freq}",
        )
        return cls._style_figure(figure, height=320)

    @classmethod
    def get_queue_depth_figure(cls, df: pandas.DataFrame, start, end, npoints=300):
        """
        Stacked area of how many items were pending vs. running over time.

        Items finished before `started_at` was tracked have an unknown start,
        so their whole lifetime is counted as running.
        """
        known_start = df["started_at"].notna()

        # pending: submitted -> started (or -> cancelled/now if never started)
        pending_mask = known_start | df["status"].isin(["P", "C"])
        pending_starts = df.loc[pending_mask, "created_at"]
        pending_ends = df.loc[pending_mask, "started_at"].fillna(
            df.loc[pending_mask, "ended_at"]
        )

        # running: started -> ended (legacy rows: submitted -> ended)
        running_mask = df["status"].isin(["R", "F", "E"])
        running_starts = df.loc[running_mask, "started_at"].fillna(
            df.loc[running_mask, "created_at"]
        )
        running_ends = df.loc[running_mask, "ended_at"]

        grid = pandas.date_range(start, end, periods=npoints)

        def depth(starts: pandas.Series, ends: pandas.Series) -> pandas.Series:
            if starts.empty:
                return pandas.Series(0, index=grid)
            deltas = pandas.concat(
                [
                    pandas.Series(1, index=starts.values),
                    pandas.Series(-1, index=ends.values),
                ]
            )
            level = deltas.groupby(level=0).sum().sort_index().cumsum()
            level = level.reindex(level.index.union(grid)).ffill().fillna(0)
            return level.loc[grid]

        figure = plotly_go.Figure()
        for label, starts, ends in [
            ("Running", running_starts, running_ends),
            ("Pending", pending_starts, pending_ends),
        ]:
            figure.add_scatter(
                x=grid,
                y=depth(starts, ends).values,
                name=label,
                mode="lines",
                line=dict(color=TIMELINE_COLORS[label], width=1, shape="hv"),
                stackgroup="depth",
            )
        figure.update_layout(
            hovermode="x unified",
            xaxis_range=[start, end],
            yaxis_title="Items",
        )
        return cls._style_figure(figure, height=320)

    @classmethod
    def get_jobs_figure(cls, df: pandas.DataFrame, start, end, limit: int = 500):
        """
        Gantt chart of the most recent items: one bar per item, one row per
        worker (plus a row for the queue), colored by status. Running bars
        cover the run time; pending bars cover the time spent in the queue.
        """
        jobs = df[df["ended_at"] >= start]
        jobs = jobs.sort_values("updated_at", ascending=False).head(limit).copy()
        if jobs.empty:
            return None

        is_pending = jobs["status"] == "P"
        jobs["bar_start"] = jobs["started_at"].fillna(jobs["created_at"])
        jobs.loc[is_pending, "bar_start"] = jobs.loc[is_pending, "created_at"]
        jobs = jobs[jobs["status"] != "C"]  # never ran, so nothing to show
        if jobs.empty:
            return None

        jobs["queue_wait"] = (
            (jobs["started_at"] - jobs["created_at"]).astype(str).str.split(".").str[0]
        )
        jobs["run_time"] = (
            (jobs["ended_at"] - jobs["bar_start"]).astype(str).str.split(".").str[0]
        )

        figure = plotly_express.timeline(
            jobs,
            x_start="bar_start",
            x_end="ended_at",
            y="row_label",
            color="status_label",
            color_discrete_map=TIMELINE_COLORS,
            hover_name="short_id",
            hover_data={
                "workflow": True,
                "queue_wait": True,
                "run_time": True,
                "status_label": False,
                "row_label": False,
                "bar_start": False,
                "ended_at": False,
            },
            labels={"status_label": "Status", "row_label": ""},
        )
        figure.update_yaxes(autorange="reversed")
        figure.update_layout(xaxis_range=[start, end])
        nrows = jobs["row_label"].nunique()
        return cls._style_figure(figure, height=min(120 + 24 * nrows, 900))

    @classmethod
    def get_durations_figure(cls, df: pandas.DataFrame, start, end, ntop: int = 10):
        """
        Box plot of queue-wait and run time (in minutes) for the most common
        workflows. Only includes finished/errored items with a known start.
        """
        done = df[
            df["status"].isin(["F", "E"])
            & df["started_at"].notna()
            & (df["ended_at"] >= start)
        ]
        if done.empty:
            return None

        top_workflows = done["workflow"].value_counts().index[:ntop]
        done = done[done["workflow"].isin(top_workflows)]

        durations = pandas.concat(
            [
                pandas.DataFrame(
                    {
                        "workflow": done["workflow"],
                        "metric": metric,
                        "minutes": (end_col - start_col).dt.total_seconds() / 60,
                    }
                )
                for metric, start_col, end_col in [
                    ("Queue wait", done["created_at"], done["started_at"]),
                    ("Run time", done["started_at"], done["ended_at"]),
                ]
            ]
        )
        # log axis can't show zeros, so clip to 1 second
        durations["minutes"] = durations["minutes"].clip(lower=1 / 60)

        figure = plotly_express.box(
            durations,
            x="workflow",
            y="minutes",
            color="metric",
            color_discrete_map=TIMELINE_COLORS,
            log_y=True,
            labels={"workflow": "", "minutes": "Minutes (log)", "metric": ""},
        )
        return cls._style_figure(figure, height=320)
