# -*- coding: utf-8 -*-

import prefect  # base import is required for prefect context
from prefect import task, Flow, Parameter
from prefect.storage import Module

from simmate.calculators.vasp.tasks.relaxation.third_party.mit import MITRelaxationTask

from simmate.configuration.django import setup_full  # sets database connection
from simmate.database.local_calculations.relaxation.mit import (
    MITRelaxationStructure,
    MITRelaxation,
)

# --------------------------------------------------------------------------------------

from pymatgen.core.structure import Structure


@task
def load_structure(structure):

    # How the structure was submitted as a parameter often depends on if we
    # are submitting to Prefect Cloud or running the flow locally. Therefore,
    # the structure parameter could be a number of formats. Here, we use a
    # task to convert the input to a pymatgen structure

    # if the input is already a pymatgen structure, just return it back
    if type(structure) == Structure:
        return structure
    # otherwise load the structure from the string and return it
    else:
        return Structure.from_str(structure, fmt="json")


# --------------------------------------------------------------------------------------


# we initialize the task here so we can use it in the Prefect flow below
relax_structure = MITRelaxationTask()


# --------------------------------------------------------------------------------------


@task
def save_input(structure):

    # initialize the MITRelaxation with the Prefect run info
    calculation = MITRelaxation.from_prefect_context(prefect.context)
    calculation.save()

    # save the intial structure to the database and link it to the calculation
    structure_start = MITRelaxationStructure.from_pymatgen(
        structure,
        ionic_step_number=0,
        relaxation=calculation,
    )
    structure_start.save()

    # and make sure this is listed as the starting structure for our calculation too.
    calculation.structure_start = structure_start
    calculation.save()

    return calculation.id


# --------------------------------------------------------------------------------------


@task
def save_results(result_and_corrections, calculation_id):

    # split our results and corrections (which are give as a tuple) into
    # separate variables
    vasprun, corrections = result_and_corrections

    # now grab our calculation from before and update it with our results
    calculation = MITRelaxation.objects.get(id=calculation_id)
    calculation.update_from_vasp_run(vasprun, corrections, MITRelaxationStructure)

    return calculation.id


# --------------------------------------------------------------------------------------

# now make the overall workflow
with Flow("MIT Relaxation") as workflow:

    # These are the input parameters for the overall workflow
    structure = Parameter("structure")
    directory = Parameter("directory", default=".")
    vasp_command = Parameter("vasp_command", default="vasp > vasp.out")

    # load the structure
    structure_pmg = load_structure(structure)

    # Add the initial structure to the database and log the Prefect information
    # for the calculation. We save the id so we know where to write results.
    calculation_id = save_input(structure_pmg)

    # Run the calculation
    result_and_corrections = relax_structure(
        structure=structure_pmg,
        directory=directory,
        command=vasp_command,
    )

    # pass these results and corrections into our final task which saves
    # everything to the database
    save_results(result_and_corrections, calculation_id)

# For when this workflow is registered with Prefect Cloud, we indicate that
# it can be imported from a python module. Note __name__ provides the path
# to this module.
workflow.storage = Module(__name__)

# --------------------------------------------------------------------------------------
