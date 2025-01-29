# -*- coding: utf-8 -*-

from simmate.engine.staged_workflow import StagedWorkflow


class StaticEnergy__Vasp__LowQuality(StagedWorkflow):
    """
    Runs a series of increasing-quality relaxations and then finishes with a single
    static energy calculation.

    This workflow is most useful for randomly-created structures or extremely
    large supercells. More precise relaxations+energy calcs should be done
    afterwards because ettings are still below MIT and Materials Project quality.
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

    description_doc_short = "runs a series of relaxations (00-04 quality)"

    subworkflow_names = [
        "relaxation.vasp.quality00",
        "relaxation.vasp.quality01",
        "relaxation.vasp.quality02",
        "relaxation.vasp.quality03",
        "relaxation.vasp.quality04",
        "static-energy.vasp.quality04",
    ]
