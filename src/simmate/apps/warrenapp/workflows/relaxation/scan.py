# -*- coding: utf-8 -*-

from simmate.apps.warrenapp.workflows.relaxation.pbe import Relaxation__Warren__Pbe


class Relaxation__Warren__Scan(Relaxation__Warren__Pbe):
    """
    Runs a VASP relaxation calculation using Warren Lab SCAN functional settings.
    """

    description_doc_short = "Warren Lab presets for SCAN geometry optimization"

    incar = Relaxation__Warren__Pbe.incar.copy()
    incar.update(
        ALGO="All",
        EDIFF=1.0e-05,
        EDIFFG=-0.02,
        ENAUG=1360,
        ENCUT=680,
        LMIXTAU=True,
        METAGGA="R2scan",
        KSPACING=0.22,
        ISMEAR=2,
        SIGMA=0.2,
        IVDW=0,  # No d3 coefficients for SCAN so we just turn of VDW corrections
    )
