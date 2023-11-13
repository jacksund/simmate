# -*- coding: utf-8 -*-

# from warrenapp.workflows.population_analysis.bader_pbe import (
#     StaticEnergy__Warren__PrebaderPbe,
# )
from simmate.apps.warrenapp.workflows.population_analysis.base import VaspBaderBase
from simmate.apps.warrenapp.workflows.population_analysis.prebader_badelf_dft import (
    StaticEnergy__Warren__PrebaderHse,
)


class PopulationAnalysis__Warren__BaderHse(VaspBaderBase):
    """
    Runs a static energy calculation using an extra-fine FFT grid using vasp
    and then carries out Bader analysis on the resulting charge density.
    Uses the Warren lab HSE settings.
    """

    static_energy_prebader = StaticEnergy__Warren__PrebaderHse
