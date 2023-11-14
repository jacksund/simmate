# -*- coding: utf-8 -*-


from simmate.engine.workflow import Workflow

from simmate.apps.warrenapp.workflows.population_analysis.base import VaspBaderBadElfBase
from simmate.apps.warrenapp.workflows.population_analysis.prebadelf_dft import (
    StaticEnergy__Warren__PrebadelfPbesol,
)


class PopulationAnalysis__Warren__BaderBadelfPbesol(VaspBaderBadElfBase):
    """
    Runs a static energy calculation using an extra-fine FFT grid using vasp
    and then carries out Badelf and Bader analysis on the resulting charge density.
    Uses the Warren lab settings Pbesol settings.
    """

    static_energy_prebadelf: Workflow = StaticEnergy__Warren__PrebadelfPbesol
