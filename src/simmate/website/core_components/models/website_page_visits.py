# -*- coding: utf-8 -*-

from django.contrib.auth.models import User

from simmate.database.base_data_types import DatabaseTable, table_column


class WebsitePageVisit(DatabaseTable):

    class Meta:
        db_table = "django_website_page_visits"

    # disable the default columns -- as we only inherit bc we want
    # the extra simmate methods such as the plotly figure rendering
    created_at = None
    updated_at = None
    source = None

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
