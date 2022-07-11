# -*- coding: utf-8 -*-

from prefect.context import FlowRunContext
from prefect import task


@task
def save_result(result):

    # Grab the database_table that we want to save the results in
    run_context = FlowRunContext.get()
    prefect_flow_run_id = str(run_context.flow_run.id)
    database_table = run_context.flow.simmate_workflow.database_table

    # split our results and corrections (which are given as a dict) into
    # separate variables
    vasprun = result["result"]
    corrections = result["corrections"]
    directory = result["directory"]

    # load the calculation entry for this workflow run. This should already
    # exist thanks to the load_input_and_register task.
    calculation = database_table.from_prefect_id(prefect_flow_run_id)

    # now update the calculation entry with our results
    calculation.update_from_vasp_run(vasprun, corrections, directory)

    return calculation.id
