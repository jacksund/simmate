# -*- coding: utf-8 -*-

from django.db import models


class SfpField(models.Field):
    description = "Sparse Integer Vector Fingerprint"

    def db_type(self, connection):
        return "sfp"
