# -*- coding: utf-8 -*-

import os
import yaml
import shutil

from simmate.utilities import get_directory, make_archive
from simmate.workflow_engine import Workflow, Parameter, ModuleStorage
from simmate.workflows.common_tasks import (
    LoadInputAndRegister,
    SaveOutputTask,
)
from simmate.workflows.utilities import get_workflow

from typing import List
from simmate.workflow_engine.supervised_staged_shell_task import S3Task
from simmate.database.base_data_types import Calculation


def s3task_to_workflow(
    name: str,
    module: str,
    project_name: str,
    s3task: S3Task,
    calculation_table: Calculation,
    register_kwargs: List[str],
):
    """
    Builds a workflow from a S3Task and it's corresponding database table.

    Very often with Simmate's S3Tasks, the workflow for a single S3Task is
    the same. The workflow is typically made of three tasks:

    1. loading the input parameters and registering the calculation
    2. running the calculation (what this S3Task does on its own)
    3. saving the calculation results

    Task 1 and 3 always use the same functions, where we just need to tell
    it which database table we are registering/saving to.

    Because of this common recipe for workflows, we use this method to make
    the workflow for us.
    """

    s3task_obj = s3task()  # Use defaults
    load_input_and_register = LoadInputAndRegister(
        workflow_name=name,
        input_obj_name="structure",
        calculation_table=calculation_table,
    )
    save_results = SaveOutputTask(calculation_table)

    with Workflow(name) as workflow:
        structure = Parameter("structure")
        command = Parameter("command", default="vasp_std > vasp.out")
        source = Parameter("source", default=None)
        directory = Parameter("directory", default=None)
        use_previous_directory = Parameter("use_previous_directory", default=False)

        structure_toolkit, directory_cleaned = load_input_and_register(
            input_obj=structure,
            command=command,
            source=source,
            directory=directory,
            use_previous_directory=use_previous_directory,
        )
        output = s3task_obj(
            structure=structure_toolkit,
            command=command,
            directory=directory_cleaned,
        )
        calculation_id = save_results(output=output)

    workflow.storage = ModuleStorage(module)
    workflow.project_name = project_name
    workflow.calculation_table = calculation_table
    workflow.result_table = calculation_table
    workflow.register_kwargs = register_kwargs
    workflow.result_task = output
    workflow.s3task = s3task

    # by default we just copy the docstring of the S3task to the workflow
    workflow.__doc__ = s3task.__doc__

    return workflow


def load_results_from_directories(
    base_directory: str = ".",
):
    """
    Goes through a given directory and finds all "simmate-task-" folders and zip
    archives present. The simmate_metadata.yaml file is used in each of these
    to load results into the database. All folders will be converted to archives
    once they've been loaded.

    Parameters
    ----------
    - `base_directory`:
        The main directory that will contain folders to archive. Defaults to the
        working directory.
    """
    # load the full path to the desired directory
    directory = get_directory(base_directory)

    # grab all files/folders in this directory and then limit this list to those
    # that are...
    #   1. folders
    #   2. start with "simmate-task-"
    #   3. haven't been modified for at least time_cutoff
    foldernames = [
        os.path.join(directory, f)
        for f in os.listdir(directory)
        if "simmate-task-" in os.path.basename(f)
    ]

    # Now go through this list and archive the folders that met the criteria
    # and load the data from each.
    for foldername in foldernames:

        # Print message for monitoring progress.
        # TODO: consider switching to tqdm
        print(f"Loading data from... \n\t{foldername}")

        # If we have a zip file, we need to unpack it before we can read results
        if not os.path.isdir(foldername):
            shutil.unpack_archive(
                filename=foldername,
                extract_dir=directory,
            )
            # remove the ".zip" ending for our folder
            foldername = foldername.removesuffix(".zip")

        # Grab the metadata file which tells us key information
        filename = os.path.join(foldername, "simmate_metadata.yaml")
        with open(filename) as file:
            metadata = yaml.full_load(file)

        # see which workflow was used -- which also tells us the database table
        workflow_name = metadata["workflow_name"]
        workflow = get_workflow(workflow_name)

        # now load the data
        results_db = workflow.result_table.from_directory(foldername)

        # use the metadata to update the other fields
        results_db.source = metadata["source"]
        results_db.prefect_flow_run_id = metadata["prefect_flow_run_id"]

        # note the directory might have been moved from when this was originally
        # ran vs where it is now. Therefore, we update the folder location here.
        results_db.directory = foldername

        # Now save the results and convert the folder to an archive
        results_db.save()
        make_archive(foldername)
