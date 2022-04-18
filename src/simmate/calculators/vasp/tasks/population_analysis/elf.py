# -*- coding: utf-8 -*-

from simmate.calculators.vasp.tasks.static_energy.materials_project import (
    MatProjStaticEnergy,
)


class MatProjELF(MatProjStaticEnergy):
    """
    Runs a static energy calculation under settings from the Materials Project
    and also writes the electron localization function (to ELFCAR).
    """

    incar = MatProjStaticEnergy.incar.copy()
    incar.update(
        LELF=True,  # writes ELFCAR
        NPAR=1,  # must be set if LELF is set to True
        # BUG: if NPAR conflicts with INCAR_parallel_settings config this
        # fails and tells the user to specify a setting
    )
