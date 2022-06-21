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

from simmate.workflow_engine import Workflow, Parameter, ModuleStorage
from simmate.workflow_engine.common_tasks import (
    load_input_and_register,
    run_customized_s3task,
    save_result,
)
from simmate.calculators.vasp.database.customized import CustomizedVASPCalculation


with Workflow("customized/vasp") as vasp_workflow:

    workflow_base = Parameter("workflow_base")
    input_parameters = Parameter("input_parameters", default={})
    updated_settings = Parameter("updated_settings", default={})
    directory = Parameter("directory", default=None)

    parameters_cleaned = load_input_and_register(
        workflow_base=workflow_base,
        input_parameters=input_parameters,
        updated_settings=updated_settings,
        directory=directory,
    )

    result = run_customized_s3task(
        workflow_base=parameters_cleaned["workflow_base"],
        input_parameters=parameters_cleaned["input_parameters"],
        updated_settings=parameters_cleaned["updated_settings"],
    )

    save_result(result)

vasp_workflow.storage = ModuleStorage(__name__)
vasp_workflow.project_name = "Simmate-Customized"
vasp_workflow.database_table = CustomizedVASPCalculation
vasp_workflow.register_kwargs = [
    "workflow_base",
    "input_parameters",
    "updated_settings",
]
vasp_workflow.result_task = result
vasp_workflow.s3task = None
vasp_workflow.__doc__ = "VASP calculation with updated INCAR/POTCAR settings"
