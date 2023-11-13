# -*- coding: utf-8 -*-

from simmate.database.workflow_results import StaticEnergy

from simmate.apps.warrenapp.workflows.static_energy.pbesol import StaticEnergy__Warren__Pbesol


class PopulationAnalysis__Warren__ElfPbesol(StaticEnergy__Warren__Pbesol):
    """
    Runs a static energy calculation under Warren lab Pbesol settings
    and also writes the electron localization function (to ELFCAR).
    """

    incar = StaticEnergy__Warren__Pbesol.incar.copy()
    incar.update(
        LELF=True,  # writes ELFCAR
        NPAR=1,  # must be set if LELF is set to True
        # BUG: if NPAR conflicts with INCAR_parallel_settings config this
        # fails and tells the user to specify a setting
    )

    # even though the category is "population-analysis", we only store
    # static energy data. So we manually set that table here.
    database_table = StaticEnergy
    # This will need to be changed for high throughput!
