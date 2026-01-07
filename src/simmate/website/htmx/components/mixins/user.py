# -*- coding: utf-8 -*-

from functools import cached_property

from django.contrib.auth.models import User

from simmate.configuration import settings


class UserInput:

    @cached_property
    def user_options(self):

        user_format = settings.website.user_format

        if user_format == "full_name":
            users = (
                User.objects.order_by("first_name")
                .values_list("id", "first_name", "last_name")
                .all()
            )
            # reformat into tuple of (value, display)
            return [(id, f"{first} {last}") for id, first, last in users]

        elif user_format == "username":
            users = (
                User.objects.order_by("username").values_list("id", "username").all()
            )
            # reformat into tuple of (value, display)
            return [(id, username) for id, username in users]

        else:
            raise Exception(f"Unknown `user_format` setting: {user_format}")
