# -*- coding: utf-8 -*-

from simmate.workflows.common import StagedWorkflow


class Badelf__VaspBaderkit__SpinBadelfHseWarren(StagedWorkflow):
    """
    Runs a static energy calculation using an extra-fine FFT grid using vasp
    and then carries out Badelf and Bader analysis on the resulting charge density.
    Uses the Warren lab settings HSE settings.
    """

    subworkflow_names = [
        "static-energy.vasp.prebadelf-hse-warren",
        "badelf.baderkit.spin-badelf",
    ]

    use_database = False
