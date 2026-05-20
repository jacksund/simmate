# -*- coding: utf-8 -*-

from simmate.workflows.common import StagedWorkflow


class Badelf__VaspBaderkit__SpinBadelfPbesolWarren(StagedWorkflow):
    """
    Runs a static energy calculation using an extra-fine FFT grid using vasp
    and then carries out Badelf and Bader analysis on the resulting charge density.
    Uses the Warren lab settings Pbesol settings.
    """

    subworkflow_names = [
        "static-energy.vasp.prebadelf-pbesol-warren",
        "badelf.baderkit.spin-badelf",
    ]

    use_database = False
