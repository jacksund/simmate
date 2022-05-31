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

import prefect

from simmate.utilities import get_directory
from simmate.workflow_engine import Workflow, Parameter, ModuleStorage, task
from simmate.workflow_engine.common_tasks import run_customized_s3task, SaveOutputTask
from simmate.calculators.vasp.database.customized import CustomizedVASPCalculation


@task
def register_calc(workflow_base, input_parameters, updated_settings, source, directory):
    # !!! This code is copied and modified from the LoadInputAndRegister task.
    # I need to merge these functions in the future.

    directory_cleaned = get_directory(directory)
    input_parameters["directory"] = directory_cleaned

    prefect_flow_run_id = prefect.context.flow_run_id

    # HACK FIX: I need to make sure everything is JSON serailizable, and I use
    # a static method from the Workflow class to do this. This may be a good
    # sign that this method should become a utility instead.
    inputs_cleaned = Workflow._serialize_parameters(**input_parameters)

    calculation = CustomizedVASPCalculation.from_prefect_id(
        id=prefect_flow_run_id,
        source=source or None,
        directory=directory_cleaned,
        workflow_base=workflow_base.name,
        input_parameters=inputs_cleaned,
        updated_settings=updated_settings,
    )

    return input_parameters


save_results = SaveOutputTask(CustomizedVASPCalculation)

with Workflow("customized/vasp") as vasp_workflow:

    workflow_base = Parameter("workflow_base")
    input_parameters = Parameter("input_parameters", default={})
    updated_settings = Parameter("updated_settings", default={})
    source = Parameter("source", default=None)
    directory = Parameter("directory", default=None)

    inputs_cleaned = register_calc(
        workflow_base=workflow_base,
        input_parameters=input_parameters,
        updated_settings=updated_settings,
        source=source,
        directory=directory,
    )

    result = run_customized_s3task(
        workflow_base=workflow_base,
        input_parameters=inputs_cleaned,
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
