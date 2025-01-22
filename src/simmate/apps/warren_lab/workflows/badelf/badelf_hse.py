# -*- coding: utf-8 -*-

from simmate.engine import StagedWorkflow


class BadElf__Badelf__BadelfHse(StagedWorkflow):
    """
    Runs a static energy calculation using an extra-fine FFT grid using vasp
    and then carries out Badelf and Bader analysis on the resulting charge density.
    Uses the Warren lab settings HSE settings.
    """

    subworkflow_names = [
        "static-energy.vasp.warren-lab-prebadelf-hse",
        "bad-elf.badelf.badelf",
    ]

    files_to_copy = ["CHGCAR", "ELFCAR", "POTCAR"]
