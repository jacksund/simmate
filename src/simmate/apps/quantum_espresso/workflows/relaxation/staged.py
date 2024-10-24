# -*- coding: utf-8 -*-

from simmate.engine.staged_workflow import StagedWorkflow


class Relaxation__QuantumEspresso__Staged(StagedWorkflow):
    """
    Runs a series of increasing-quality relaxations and then finishes with a single
    static energy calculation.

    This workflow is most useful for randomly-created structures or extremely
    large supercells. More precise relaxations+energy calcs should be done
    afterwards because ettings are still below MIT and Materials Project quality.
    """

    # !!! Needs to be implemented
    exclude_from_archives = []

    description_doc_short = "runs a series of relaxations (00-04 quality)"

    subworkflow_names = [
        "relaxation.quantum-espresso.quality00",
        "relaxation.quantum-espresso.quality01",
        "relaxation.quantum-espresso.quality02",
        "relaxation.quantum-espresso.quality03",
        "relaxation.quantum-espresso.quality04",
        "static-energy.quantum-espresso.quality04",
    ]
