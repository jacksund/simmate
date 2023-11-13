# -*- coding: utf-8 -*-

# from warrenapp.workflows.population_analysis.badelf_pbe import (
#     StaticEnergy__Warren__PrebadelfPbe,
# )
from simmate.apps.warrenapp.workflows.population_analysis.base import VaspBadElfBase

# from warrenapp.workflows.static_energy import StaticEnergy__Warren__SeededHse
from simmate.apps.warrenapp.workflows.population_analysis.prebader_badelf_dft import (
    StaticEnergy__Warren__PrebadelfHse,
)


class PopulationAnalysis__Warren__BadelfHse(VaspBadElfBase):
    """
    Runs a static energy calculation using an extra-fine FFT grid and then
    carries out Bader analysis on the resulting charge density using the ELFCAR
    as a reference when partitioning. Uses the HSE functional and settings from
    the Warren Lab.
    """

    static_energy_prebadelf = StaticEnergy__Warren__PrebadelfHse
