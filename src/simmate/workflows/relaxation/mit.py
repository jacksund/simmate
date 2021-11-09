# -*- coding: utf-8 -*-

from simmate.calculators.vasp.tasks.relaxation.third_party.mit import MITRelaxationTask
from simmate.workflows.common_tasks.load_structure import load_structure

from simmate.configuration.django import setup_full  # sets database connection
from simmate.database.local_calculations.relaxation.mit import (
    MITIonicStep,
    MITRelaxation,
)

from simmate.workflow_engine.prefect import (
    prefect,
    Workflow,
    task,
    Parameter,
    ModuleStorage,
)

# --------------------------------------------------------------------------------------

# THIS SECTION SETS UP OUR TASKS

# we initialize the task here so we can use it in the Prefect flow below
relax_structure = MITRelaxationTask()


@task
def save_results(result_and_corrections):

    # split our results and corrections (which are given as a tuple) into
    # separate variables
    vasprun, corrections = result_and_corrections

    # load/create the calculation for this workflow run
    calculation = MITRelaxation.from_prefect_id(prefect.context.flow_run_id)

    # now update the calculation entry with our results
    calculation.update_from_vasp_run(vasprun, corrections, MITIonicStep)

    return calculation.id


# --------------------------------------------------------------------------------------

# THIS SECTION PUTS OUR TASKS TOGETHER TO MAKE A WORKFLOW

# now make the overall workflow
with Workflow("MIT Relaxation") as workflow:

    # These are the input parameters for the overall workflow
    structure = Parameter("structure")
    vasp_command = Parameter("vasp_command", default="vasp > vasp.out")

    # load the structure to a pymatgen object
    structure_pmg = load_structure(structure)

    # Run the calculation after we have saved the input
    result_and_corrections = relax_structure(
        structure=structure_pmg,
        command=vasp_command,
    )

    # pass these results and corrections into our final task which saves
    # everything to the database
    calculation_id = save_results(result_and_corrections)
# For when this workflow is registered with Prefect Cloud, we indicate that
# it can be imported from a python module. Note __name__ provides the path
# to this module.
workflow.storage = ModuleStorage(__name__)
workflow.project_name = "Simmate-Relaxation"
workflow.calculation_table = MITRelaxation

# --------------------------------------------------------------------------------------
