# -*- coding: utf-8 -*-

"""
Example use:
``` python
from simmate.toolkit import Structure
from simmate.workflows.static_energy import mit_workflow

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
from simmate.workflow_engine.common_tasks import run_customized_s3task, SaveOutputTask
from simmate.calculators.vasp.database.customized import CustomizedVASPCalculation


save_results = SaveOutputTask(CustomizedVASPCalculation)

with Workflow("customized/vasp") as vasp_workflow:

    workflow_base = Parameter("workflow_base")
    input_parameters = Parameter("input_parameters", default={})
    updated_settings = Parameter("updated_settings", default={})

    # NOTE: these runs are not stored in the database unless they complete
    # successfully. I may add a register() task in the future though.

    result = run_customized_s3task(
        workflow_base=workflow_base,
        input_parameters=input_parameters,
        updated_settings=updated_settings,
    )

    save_results(result)

vasp_workflow.storage = ModuleStorage(__name__)
vasp_workflow.project_name = "Simmate-Customized"
vasp_workflow.calculation_table = CustomizedVASPCalculation
vasp_workflow.result_table = CustomizedVASPCalculation
vasp_workflow.register_kwargs = {}
vasp_workflow.result_task = result
vasp_workflow.s3task = None
vasp_workflow.__doc__ = "VASP calculation with updated INCAR/POTCAR settings"
