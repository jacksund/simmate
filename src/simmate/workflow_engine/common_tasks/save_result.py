# -*- coding: utf-8 -*-

import prefect
from prefect import task


@task
def save_result(result):
    # ---------------------------------------------------------------------

    # Grab the workflow object as we need to reference some of its attributes

    # BUG: for some reason, this script fails when get_workflow is imported
    # at the top of this file rather than here.
    from simmate.workflows.utilities import get_workflow

    workflow_name = prefect.context.get("flow_name")
    workflow = get_workflow(workflow_name)

    # ---------------------------------------------------------------------

    # split our results and corrections (which are given as a dict) into
    # separate variables
    vasprun = result["result"]
    corrections = result["corrections"]
    directory = result["directory"]

    # load the calculation entry for this workflow run. This should already
    # exist thanks to the load_input_and_register task.
    calculation = workflow.database_table.from_prefect_id(
        prefect.context.flow_run_id,
    )

    # now update the calculation entry with our results
    calculation.update_from_vasp_run(vasprun, corrections, directory)

    return calculation.id
