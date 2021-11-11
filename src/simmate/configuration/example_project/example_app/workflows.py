# -*- coding: utf-8 -*-

import prefect  # base import is required for prefect context
from prefect import task, Flow, Parameter
from prefect.storage import Module

from simmate.calculators.vasp.tasks.relaxation.third_party.mit import MITRelaxationTask
from simmate.workflows.common_tasks.all import load_input

from simmate.configuration.django import setup_full  # sets database connection
from simmate.database.local_calculations.relaxation.all import (
    MITIonicStep,
    MITRelaxation,
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

    # initialize the MITRelaxation with the Prefect run info
    calculation = MITRelaxation.from_prefect_context(prefect.context)
    calculation.save()

    # now update the calculation entry with our results
    calculation.update_from_vasp_run(vasprun, corrections, MITIonicStep)

    return calculation.id


# --------------------------------------------------------------------------------------

# THIS SECTION PUTS OUR TASKS TOGETHER TO MAKE A WORKFLOW

# now make the overall workflow
with Flow("MIT Relaxation") as workflow:

    # These are the input parameters for the overall workflow
    structure = Parameter("structure")
    vasp_command = Parameter("vasp_command", default="vasp > vasp.out")

    # load the structure to a pymatgen object
    structure_pmg = load_input(structure)

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
workflow.storage = Module(__name__)

# --------------------------------------------------------------------------------------
