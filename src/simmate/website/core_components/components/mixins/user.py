# -*- coding: utf-8 -*-

from django.contrib.auth.models import User
from django_unicorn.components import UnicornView


class UserInput(UnicornView):

    class Meta:
        javascript_exclude = ("user_options",)

    @property
    def user_options(self):
        # query for all user names
        users = (
            User.objects.order_by("first_name")
            .values_list("id", "first_name", "last_name")
            .all()
        )

        # reformat into tuple of (value, display)
        return [(id, f"{first} {last}") for id, first, last in users]

    # -------------------------------------------------------------------------

    # Requires extra config such as:

    # requested_by_id = None

    # def mount(self):
    #     # set default starting values
    #     self.requested_by_id = self.request.user.id

    # -------------------------------------------------------------------------
