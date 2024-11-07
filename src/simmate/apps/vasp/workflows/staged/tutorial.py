# -*- coding: utf-8 -*-

from simmate.engine.staged_workflow import StagedWorkflow



class StagedCalculation__Vasp__EvoTutorial(StagedWorkflow):
    """
    Runs a series of increasing-quality relaxations and then finishes with a single
    static energy calculation.

    This workflow is designed exclusively for testing/tutorials where it is
    desireable to have calculations take very little time. The results
    will be VERY unreasonable.
    """

    exclude_from_archives = [
        "CHG",
        "CHGCAR",
        "DOSCAR",
        "EIGENVAL",
        "IBZKPT",
        "OSZICAR",
        "OUTCAR",
        "PCDAT",
        "POTCAR",
        "REPORT",
        "WAVECAR",
        "XDATCAR",
    ]

    description_doc_short = "runs a series of relaxations (00-01 quality)"

    subworkflow_names = [
        "relaxation.vasp.quality00",
        "relaxation.vasp.quality01",
        "relaxation.vasp.quality02",
    ]


