# -*- coding: utf-8 -*-

from simmate.apps.warrenapp.workflows.population_analysis.base import VaspBadElfBase
from simmate.apps.warrenapp.workflows.population_analysis.prebader_badelf_dft import (
    StaticEnergy__Warren__PrebadelfPbesol,
)


class PopulationAnalysis__Warren__BadelfPbesol(VaspBadElfBase):
    """
    Runs a static energy calculation using an extra-fine FFT grid and then
    carries out Bader analysis on the resulting charge density using the ELFCAR
    as a reference when partitioning. Uses the PBE functional and settings from
    the Warren Lab.
    """

    static_energy_prebadelf = StaticEnergy__Warren__PrebadelfPbesol
