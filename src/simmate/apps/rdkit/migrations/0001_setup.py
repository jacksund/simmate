# -*- coding: utf-8 -*-

from django.db import migrations

from simmate.apps.rdkit.operations import RDKitExtension
from simmate.config import settings


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [RDKitExtension()] if settings.postgres_rdkit_extension else []
