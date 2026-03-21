# -*- coding: utf-8 -*-

from django.contrib.auth.models import User

from simmate.database.core import DatabaseTable, table_column


class Feedback(DatabaseTable):

    class Meta:
        db_table = "django_website_feedback"

    user = table_column.ForeignKey(
        User,
        on_delete=table_column.CASCADE,
        null=True,
        blank=True,
        related_name="website_feedback",
    )
    """
    The user that submitted the feedback. Note, this is an optional field
    because the site might be configured to allow anonymous browsing.
    """

    message = table_column.TextField()
    """
    The feedback message submitted by the user.
    """

    url_path = table_column.TextField(null=True, blank=True)
    """
    The URL of the page where the user submitted the feedback.
    """
