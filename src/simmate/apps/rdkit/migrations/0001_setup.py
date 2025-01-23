# -*- coding: utf-8 -*-

from django.db import migrations

from simmate.apps.rdkit.operations import RDKitExtension


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [RDKitExtension()]
