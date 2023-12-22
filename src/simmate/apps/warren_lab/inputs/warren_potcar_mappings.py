# -*- coding: utf-8 -*-
from simmate.apps.vasp.inputs.potcar_mappings import PBE_POTCAR_MAPPINGS

HSE_POTCAR_MAPPINGS = PBE_POTCAR_MAPPINGS.copy()
HSE_POTCAR_MAPPINGS.update(
    {
        "Dy": "Dy",
        "Er": "Er",
        "Ho": "Ho",
        "Nd": "Nd",
        "Sm": "Sm",
        "Tb": "Tb",
    }
)
