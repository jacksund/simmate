# -*- coding: utf-8 -*-

from django.contrib.auth.models import User

from simmate.database.core import DatabaseTable, table_column


class Notification(DatabaseTable):
    """
    A notification for a specific user.
    """

    class Meta:
        db_table = "simmate_notifications"

    user = table_column.ForeignKey(
        User,
        on_delete=table_column.CASCADE,
        related_name="notifications",
    )
    """
    The user that this notification is for.
    """

    message = table_column.TextField()
    """
    The content of the notification.
    """

    notification_type = table_column.CharField(max_length=100)
    """
    The type of notification (e.g., 'workflow_complete', 'system_alert').
    This is used for grouping notifications.
    """

    is_read = table_column.BooleanField(default=False)
    """
    Whether the notification has been read by the user.
    """

    target_url = table_column.CharField(max_length=500, null=True, blank=True)
    """
    An optional URL that the user should be directed to when clicking the notification.
    """

    @classmethod
    def create_notification(
        cls,
        user: User,
        message: str,
        notification_type: str,
        target_url: str = None,
    ):
        """
        A helper method to create a new notification for a user.
        """
        notification = cls(
            user=user,
            message=message,
            notification_type=notification_type,
            target_url=target_url,
        )
        notification.save()
        return notification
