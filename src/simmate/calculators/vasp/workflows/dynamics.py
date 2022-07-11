# -*- coding: utf-8 -*-

from simmate.toolkit import Structure
from simmate.workflow_engine import Workflow
from simmate.workflow_engine.common_tasks import (
    load_input_and_register,
    save_result,
)
from simmate.calculators.vasp.tasks.dynamics import MITDynamics
from simmate.calculators.vasp.database.dynamics import MITDynamicsRun


class Dynamics__Vasp__Mit(Workflow):
    description_doc_short = "uses MIT Project settings"
    database_table = MITDynamicsRun
    s3task = MITDynamics

    @classmethod
    def run_config(
        cls,
        structure: Structure,
        command: str = None,
        source: dict = None,
        directory: str = None,
        #
        # extra parameters unique to molecular dynamics runs
        copy_previous_directory: bool = False,
        temperature_start: float = 300,
        temperature_end: float = 1200,
        time_step: float = 2,
        nsteps: int = 10000,
    ):
        parameters_cleaned = load_input_and_register(
            structure=structure,
            source=source,
            directory=directory,
            command=command,
            copy_previous_directory=copy_previous_directory,
            temperature_start=temperature_start,
            temperature_end=temperature_end,
            time_step=time_step,
            nsteps=nsteps,
        ).result()

        result = cls.s3task.run(**parameters_cleaned).result()
        calculation_id = save_result(result)

        return result
