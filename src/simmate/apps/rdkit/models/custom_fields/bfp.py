# -*- coding: utf-8 -*-


from django.db import models


class BfpField(models.Field):
    description = "Binary Fingerprint"

    def db_type(self, connection):
        return "bfp"
