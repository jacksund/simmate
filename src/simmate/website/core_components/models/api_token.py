# -*- coding: utf-8 -*-

import binascii
import os

from django.conf import settings

from simmate.database.base_data_types import DatabaseTable, table_column


class ApiToken(DatabaseTable):
    """
    The default authorization token model.

    This is forked from...
        `from rest_framework.authtoken.models import Token`
    """

    class Meta:
        # while this might be misleading for django admins, it's where people
        # expect the tokens to be in the database. There's no overlapping table
        # with this name so it's safe.
        db_table = "auth_token"

    # disable default cols
    id = None  # we want the api key itself to be the primary key

    key = table_column.CharField(max_length=40, primary_key=True)

    user = table_column.OneToOneField(
        settings.AUTH_USER_MODEL,  # django.contrib.auth.models.User
        related_name="auth_token",
        on_delete=table_column.CASCADE,
    )

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = self.generate_key()
        return super().save(*args, **kwargs)

    @staticmethod
    def generate_key():
        return binascii.hexlify(os.urandom(20)).decode()
