# -*- coding: utf-8 -*-

import os

from simmate.workflow_engine import Workflow
from simmate.workflow_engine.common_tasks import load_input_and_register
from simmate.calculators.vasp.workflows.relaxation.quality00 import (
    Relaxation__VASP__Quality00,
)
from simmate.calculators.vasp.workflows.relaxation.quality01 import (
    Relaxation__VASP__Quality01,
)
from simmate.calculators.vasp.workflows.relaxation.quality02 import (
    Relaxation__VASP__Quality02,
)
from simmate.calculators.vasp.workflows.relaxation.quality03 import (
    Relaxation__VASP__Quality03,
)
from simmate.calculators.vasp.workflows.relaxation.quality04 import (
    Relaxation__VASP__Quality04,
)
from simmate.calculators.vasp.workflows.static_energy.quality04 import (
    Static_Energy__VASP__Quality04,
)

from simmate.calculators.vasp.database.relaxation import StagedRelaxation


class Relaxation__VASP__Staged(Workflow):
    """
    Runs a series of increasing-quality relaxations and then finishes with a single
    static energy calculation.

    This is therefore a "Nested Workflow" made of the following smaller workflows:

        - relaxation/quality00
        - relaxation/quality01
        - relaxation/quality02
        - relaxation/quality03
        - relaxation/quality04
        - static-energy/quality04

    This workflow is most useful for randomly-created structures or extremely
    large supercells. More precise relaxations+energy calcs should be done
    afterwards because ettings are still below MIT and Materials Project quality.
    """

    description_doc_short = "runs a series of relaxations (00-04 quality)"
    database_table = StagedRelaxation

    @staticmethod
    def run(
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
        )
        
        # Our first relaxation is directly from our inputs. The remaining one
        # pass along results
        recent_task = Relaxation__VASP__Quality00
        recent_state = recent_task.run_as_prefect_flow(
            structure=parameters_cleaned["structure"],
            command=parameters_cleaned["command"],
            directory=parameters_cleaned["directory"] + os.path.sep + recent_task.name,
        )
        recent_result = recent_state.result()
        
        # The remaining tasks continue and use the past results as an input
        for i, current_task in enumerate([
            Relaxation__VASP__Quality01,
            Relaxation__VASP__Quality02,
            Relaxation__VASP__Quality03,
            Relaxation__VASP__Quality04,
            Static_Energy__VASP__Quality04,
        ]):
            recent_state = current_task.run_as_prefect_flow(
                structure={
                    "database_table": recent_task.database_table.__name__,
                    "directory": recent_result["directory"],
                    "structure_field": "structure_final",
                },
                command=parameters_cleaned["command"],
                directory=parameters_cleaned["directory"] + os.path.sep + current_task.name,
            )
            recent_result = recent_state.result()
        
        # return the result of the final static energy if the user wants it
        return recent_result
