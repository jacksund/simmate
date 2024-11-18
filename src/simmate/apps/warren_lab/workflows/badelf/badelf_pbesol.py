# -*- coding: utf-8 -*-

from simmate.engine import StagedWorkflow


class StagedCalculation__Badelf__BadelfPbesol(StagedWorkflow):
    """
    Runs a static energy calculation using an extra-fine FFT grid using vasp
    and then carries out Badelf and Bader analysis on the resulting charge density.
    Uses the Warren lab settings Pbesol settings.
    """

    subworkflow_names = [
        "static-energy.vasp.warren-lab-prebadelf-pbesol",
        "bad-elf.badelf.badelf",
    ]

    one_folder = True
