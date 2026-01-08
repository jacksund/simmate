# -*- coding: utf-8 -*-

from simmate.apps.warren_lab.workflows.static_energy.pre_bader_badelf import (
    StaticEnergy__Vasp__PrebadelfPbesolWarren,
)
from simmate.workflows.base_flow_types import StagedWorkflow


class Badelf__VaspBaderkit__SpinBadelfPbesolWarren(StagedWorkflow):
    """
    Runs a static energy calculation using an extra-fine FFT grid using vasp
    and then carries out Badelf and Bader analysis on the resulting charge density.
    Uses the Warren lab settings Pbesol settings.
    """

    subworkflow_names = [
        StaticEnergy__Vasp__PrebadelfPbesolWarren,
        "badelf.baderkit.spin-badelf",
    ]

    use_database = False
