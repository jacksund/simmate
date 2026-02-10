# -*- coding: utf-8 -*-

import numpy
import pandas
import plotly.express as plotly_express
import plotly.graph_objects as plotly_go
from django.contrib.auth.models import User
from plotly.subplots import make_subplots

from simmate.database.base_data_types import DatabaseTable, table_column


class WebsitePageVisit(DatabaseTable):

    class Meta:
        db_table = "django_website_page_visits"

    html_entries_template = "core_components/website_page_visits/table.html"

    # disable the default columns -- as we only inherit bc we want
    # the extra simmate methods such as the plotly figure rendering
    created_at = None
    updated_at = None

    user = table_column.ForeignKey(
        User,
        on_delete=table_column.CASCADE,
        null=True,
        blank=True,
        related_name="website_page_visits",
    )
    """
    The user that visited the website. Note, this is an optional field
    because (1) the user might not be signed in yet or (2) the site is
    configured to allow anonymous browsing
    """

    url_path = table_column.TextField()
    """
    The base URL of the page visited -- so not including the hostname and GET
    parameters.
    
    For example if the page visited was "example.com/path/to/page/?setting=123",
    then this column would be "path/to/page"
    """

    url_parameters = table_column.JSONField(null=True, blank=True)
    """
    The GET URL parameters of the page visited, stored as JSON
    
    For example if the page visited was "example.com/path/to/page/?setting=123",
    then this column would be "{'setting': 123}"
    """

    timestamp = table_column.DateTimeField(
        auto_now=True,
        db_index=True,
    )
    """
    The exact date and time that the page was visited.
    """

    # -------------------------------------------------------------------------

    enable_html_report = True
    report_df_columns = ["user_id", "url_path", "timestamp"]

    @classmethod
    def get_report_from_df(cls, df: pandas.DataFrame):
        return {
            "unique_users_and_traffic": cls.get_unique_users_and_traffic(df),
            "most_visited_pages": cls.get_most_visited_pages(df),
        }

    @classmethod
    def get_most_visited_pages(cls, df: pandas.DataFrame, ntop: int = 10):
        url_counts = df["url_path"].value_counts().nlargest(ntop)
        top_urls_df = pandas.DataFrame(
            {"url_path": url_counts.index, "visits": url_counts.values}
        )
        fig = plotly_express.bar(
            top_urls_df,
            x="url_path",
            y="visits",
            labels={
                "url_path": "URL",
                "visits": "Visits (#)",
            },
        )
        return fig

    @classmethod
    def get_unique_users_and_traffic(cls, df: pandas.DataFrame):

        # --- Data Preparation ---

        # Daily aggregation
        df["date"] = df["timestamp"].dt.date
        daily_users = df.groupby("date")["user_id"].nunique().reset_index()
        daily_users.rename(columns={"user_id": "unique_users"}, inplace=True)

        # Weekly aggregation
        df["week"] = (
            df["timestamp"].dt.to_period("W").apply(lambda r: r.start_time.date())
        )
        weekly_users = df.groupby("week")["user_id"].nunique().reset_index()
        weekly_users.rename(columns={"user_id": "unique_users"}, inplace=True)

        # Monthly aggregation
        df["month"] = (
            df["timestamp"].dt.to_period("M").apply(lambda r: r.start_time.date())
        )
        monthly_users = df.groupby("month")["user_id"].nunique().reset_index()
        monthly_users.rename(columns={"user_id": "unique_users"}, inplace=True)

        # --- Histogram Preparation (2-hour bins) ---

        min_date = df["timestamp"].min()
        max_date = df["timestamp"].max()
        total_hours = (max_date - min_date).total_seconds() / 3600
        nbins = int(int(total_hours) / 2)  # 2-hour bins

        # Create bin edges
        bin_edges = pandas.date_range(start=min_date, end=max_date, periods=nbins + 1)
        # Bin the timestamps
        hist_counts, _ = numpy.histogram(df["timestamp"], bins=bin_edges)

        # For bar plotting, use the left edge of each bin
        hist_x = bin_edges[:-1]
        hist_y = hist_counts
        if hist_x.empty:
            bin_width_ms = 10_000
        else:
            bin_width_ms = (
                hist_x[1] - hist_x[0]
            ).total_seconds() * 1000  # width in milliseconds

        # --- Plotting ---

        fig = make_subplots(
            rows=4,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
        )

        # Monthly users (row 1)
        fig.add_trace(
            plotly_go.Bar(
                x=monthly_users["month"],
                y=monthly_users["unique_users"],
            ),
            row=1,
            col=1,
        )

        # Weekly users (row 2)
        fig.add_trace(
            plotly_go.Bar(
                x=weekly_users["week"],
                y=weekly_users["unique_users"],
            ),
            row=2,
            col=1,
        )

        # Daily users (row 3)
        fig.add_trace(
            plotly_go.Bar(
                x=daily_users["date"],
                y=daily_users["unique_users"],
            ),
            row=3,
            col=1,
        )

        # 2-hour histogram (row 4)
        fig.add_trace(
            plotly_go.Bar(
                x=hist_x,
                y=hist_y,
                width=bin_width_ms,
            ),
            row=4,
            col=1,
        )

        fig.update_layout(
            height=500,
            showlegend=False,
            xaxis4=dict(title="Date"),
            yaxis1=dict(title="Monthly Users"),
            yaxis2=dict(title="Weekly Users"),
            yaxis3=dict(title="Daily Users"),
            yaxis4=dict(title="Total Visits"),
            bargap=0.1,
        )

        return fig
