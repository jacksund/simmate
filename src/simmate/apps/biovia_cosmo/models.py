# -*- coding: utf-8 -*-

from simmate.apps.rdkit.models import Molecule
from simmate.database.core import table_column
from simmate.database.mixins import Calculation


class LogPow(Molecule, Calculation):
    # class Meta:
    #     app_label = "workflows"  <-- future app once open-sourced

    log_p = table_column.FloatField(null=True, blank=True)
