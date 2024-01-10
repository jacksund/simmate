# -*- coding: utf-8 -*-

from simmate.apps.badelf.workflows.badelf import BadElf__Badelf__Badelf
from simmate.apps.badelf.workflows.base import VaspBadElfBase
from simmate.apps.warren_lab.workflows.badelf.prebadelf_dft import (
    StaticEnergy__Vasp__WarrenLabPrebadelfPbesol,
)


class BadElf__Badelf__BadelfPbesol(VaspBadElfBase):
    """
    Runs a static energy calculation using an extra-fine FFT grid using vasp
    and then carries out Badelf and Bader analysis on the resulting charge density.
    Uses the Warren lab settings Pbesol settings.
    """

    static_energy_workflow = StaticEnergy__Vasp__WarrenLabPrebadelfPbesol
    badelf_workflow = BadElf__Badelf__Badelf
