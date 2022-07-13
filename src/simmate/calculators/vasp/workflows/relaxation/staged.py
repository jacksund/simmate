# -*- coding: utf-8 -*-

import os

from simmate.workflow_engine import Workflow
from simmate.workflow_engine.common_tasks import load_input_and_register
from simmate.calculators.vasp.workflows.relaxation.quality00 import (
    Relaxation__Vasp__Quality00,
)
from simmate.calculators.vasp.workflows.relaxation.quality01 import (
    Relaxation__Vasp__Quality01,
)
from simmate.calculators.vasp.workflows.relaxation.quality02 import (
    Relaxation__Vasp__Quality02,
)
from simmate.calculators.vasp.workflows.relaxation.quality03 import (
    Relaxation__Vasp__Quality03,
)
from simmate.calculators.vasp.workflows.relaxation.quality04 import (
    Relaxation__Vasp__Quality04,
)
from simmate.calculators.vasp.workflows.static_energy.quality04 import (
    StaticEnergy__Vasp__Quality04,
)

from simmate.calculators.vasp.database.relaxation import StagedRelaxation


class Relaxation__Vasp__Staged(Workflow):
    """
    Runs a series of increasing-quality relaxations and then finishes with a single
    static energy calculation.

    This is therefore a "Nested Workflow" made of the following smaller workflows:

        - relaxation.vasp.quality00
        - relaxation.vasp.quality01
        - relaxation.vasp.quality02
        - relaxation.vasp.quality03
        - relaxation.vasp.quality04
        - static-energy.vasp.quality04

    This workflow is most useful for randomly-created structures or extremely
    large supercells. More precise relaxations+energy calcs should be done
    afterwards because ettings are still below MIT and Materials Project quality.
    """

    description_doc_short = "runs a series of relaxations (00-04 quality)"
    database_table = StagedRelaxation

    @staticmethod
    def run_config(
        structure,
        command=None,
        source=None,
        directory=None,
        copy_previous_directory=False,
    ):

        parameters_cleaned = load_input_and_register(
            structure=structure,
            command=command,
            source=source,
            directory=directory,
            copy_previous_directory=copy_previous_directory,
        ).result()

        tasks_to_run = [
            Relaxation__Vasp__Quality00,
            Relaxation__Vasp__Quality01,
            Relaxation__Vasp__Quality02,
            Relaxation__Vasp__Quality03,
            Relaxation__Vasp__Quality04,
            StaticEnergy__Vasp__Quality04,
        ]

        # Our first relaxation is directly from our inputs.
        current_task = tasks_to_run[0]
        state = current_task.run(
            structure=parameters_cleaned["structure"],
            command=parameters_cleaned.get("command"),
            directory=parameters_cleaned["directory"]
            + os.path.sep
            + current_task.name_full,
        )
        result = state.result()

        # The remaining tasks continue and use the past results as an input
        for i, current_task in enumerate(tasks_to_run[1:]):
            preceding_task = tasks_to_run[i]  # will be one before because of [:1]
            state = current_task.run(
                structure={
                    "database_table": preceding_task.database_table.__name__,
                    "directory": result["directory"],  # uses preceding result
                    "structure_field": "structure_final",
                },
                command=parameters_cleaned.get("command"),
                directory=parameters_cleaned["directory"]
                + os.path.sep
                + current_task.name_full,
            )
            result = state.result()

        # return the result of the final static energy if the user wants it
        return result
