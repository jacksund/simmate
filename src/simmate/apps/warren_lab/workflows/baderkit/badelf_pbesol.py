# -*- coding: utf-8 -*-

from simmate.apps.badelf.models import BadElf
from simmate.database import connect
from simmate.workflows.base_flow_types import StagedWorkflow


class BadElf__Badelf__BadelfPbesol(StagedWorkflow):
    """
    Runs a static energy calculation using an extra-fine FFT grid using vasp
    and then carries out Badelf and Bader analysis on the resulting charge density.
    Uses the Warren lab settings Pbesol settings.
    """

    subworkflow_names = [
        "static-energy.vasp.warren-lab-prebadelf-pbesol",
        "spin-badelf.badelf.badelf",
    ]

    files_to_copy = ["CHGCAR", "ELFCAR", "POTCAR"]

    database_table = BadElf
