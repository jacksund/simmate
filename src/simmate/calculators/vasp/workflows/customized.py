# -*- coding: utf-8 -*-

"""
Example use:
``` python
from simmate.toolkit import Structure
from simmate.workflows.static_energy import mit_workflow
from simmate.workflows.customized import vasp_workflow

s = Structure(
    lattice=[
        [3.485437, 0.0, 2.012318],
        [1.161812, 3.286101, 2.012318],
        [0.0, 0.0, 4.024635],
    ],
    species=["Na", "Cl"],
    coords=[[0.0, 0.0, 0.0], [0.5, 0.5, 0.5]],
)

vasp_workflow.run(
    workflow_base=mit_workflow,
    input_parameters={"structure": s},
    updated_settings={
        "incar": {"NPAR": 1, "ENCUT": 600},
    },
)
```
"""

from simmate.workflow_engine import Workflow
from simmate.workflow_engine.common_tasks import (
    load_input_and_register,
    run_customized_s3task,
    save_result,
)
from simmate.calculators.vasp.database.customized import (
    CustomizedVASPCalculation,
)


class Customized__Vasp__UserConfig(Workflow):
    """
    "VASP calculation with updated INCAR/POTCAR settings
    """

    database_table = CustomizedVASPCalculation

    @staticmethod
    def run_config(
        workflow_base: str,
        input_parameters: dict,
        updated_settings: dict,
    ):
        parameters_cleaned = load_input_and_register(
            workflow_base=workflow_base,
            input_parameters=input_parameters,
            updated_settings=updated_settings,
        ).result()

        result = run_customized_s3task(**parameters_cleaned)

        save_result(result)
