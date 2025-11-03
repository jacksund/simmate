# -*- coding: utf-8 -*-

from functools import cached_property

from django.contrib.auth.models import User


class UserInput:

    @cached_property
    def user_options(self):
        # # query for all user names
        # users = (
        #     User.objects.order_by("first_name")
        #     .values_list("id", "first_name", "last_name")
        #     .all()
        # )
        # # reformat into tuple of (value, display)
        # return [(id, f"{first} {last}") for id, first, last in users]

        # TODO: add settings flag to make the dropdown usernames vs full
        users = User.objects.order_by("first_name").values_list("id", "username").all()
        # reformat into tuple of (value, display)
        return [(id, username) for id, username in users]

    # -------------------------------------------------------------------------

    # Requires extra config such as:

    # requested_by_id = None

    # def mount(self):
    #     # set default starting values
    #     self.requested_by_id = self.request.user.id

    # ------------------------------------------------------------------------
