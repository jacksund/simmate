# -*- coding: utf-8 -*-

from simmate.apps.warrenapp.workflows.population_analysis.badelf_pbesol import (
    StaticEnergy__Warren__PrebadelfPbesol,
)
from simmate.apps.warrenapp.workflows.population_analysis.base import VaspBaderBase
from simmate.apps.warrenapp.workflows.population_analysis.prebader_badelf_dft import (
    StaticEnergy__Warren__PrebaderPbesol,
)


class PopulationAnalysis__Warren__BaderPbesol(VaspBaderBase):
    """
    Runs a static energy calculation using an extra-fine FFT grid using vasp
    and then carries out Bader analysis on the resulting charge density.
    Uses the Warren lab settings Pbesol settings.
    """

    static_energy_prebader = StaticEnergy__Warren__PrebaderPbesol
    static_energy_prebadelf = StaticEnergy__Warren__PrebadelfPbesol
