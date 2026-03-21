# -*- coding: utf-8 -*-


from django.core.mail import EmailMultiAlternatives
from django.utils.log import AdminEmailHandler


class SuperUserEmailHandler(AdminEmailHandler):
    def send_mail(self, subject, message, *args, **kwargs):
        """
        Override the send_mail method to fetch recipients from the DB
        instead of settings.ADMINS.
        """

        from django.contrib.auth.models import User

        # Query for active superusers with emails
        recipient_list = list(
            User.objects.filter(
                is_superuser=True,
                is_active=True,
                email__isnull=False,
            ).values_list("email", flat=True)
        )

        if not recipient_list:
            return

        email = EmailMultiAlternatives(
            subject=subject,
            body=message,  # The plain text stack trace
            to=recipient_list,
        )

        # Attach the HTML version if it exists
        # kwargs['html_message'] contains the "Yellow Page" debug HTML
        if kwargs.get("html_message"):
            email.attach_alternative(kwargs["html_message"], "text/html")

        email.send(fail_silently=True)
