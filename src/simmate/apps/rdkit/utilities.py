# -*- coding: utf-8 -*-

import simmate.apps.rdkit.models.custom_fields.bfp
import simmate.apps.rdkit.models.custom_fields.mol
from simmate.configuration import settings


def get_rdkit_ext_fields():
    rdkit_fields = [
        (
            "rdkit_mol",
            simmate.apps.rdkit.models.custom_fields.mol.MolField(blank=True, null=True),
        ),
        (
            "fingerprint_morganbv",
            simmate.apps.rdkit.models.custom_fields.bfp.BfpField(blank=True, null=True),
        ),
    ]
    return rdkit_fields if settings.postgres_rdkit_extension else []
