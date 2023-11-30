# -*- coding: utf-8 -*-

from simmate.apps.warrenapp.workflows.badelf.base import VaspBadElfBase
from simmate.apps.warrenapp.workflows.badelf.prebadelf_dft import (
    StaticEnergy__Warren__PrebadelfHse,
)
from simmate.apps.warrenapp.workflows.badelf.badelf import BadElfAnalysis__Warren__Badelf


class BadElfAnalysis__Warren__BadelfHse(VaspBadElfBase):
    """
    Runs a static energy calculation using an extra-fine FFT grid using vasp
    and then carries out Badelf and Bader analysis on the resulting charge density.
    Uses the Warren lab settings HSE settings.
    """

    static_energy_workflow = StaticEnergy__Warren__PrebadelfHse
    badelf_workflow = BadElfAnalysis__Warren__Badelf
