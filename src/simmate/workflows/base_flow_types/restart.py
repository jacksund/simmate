# -*- coding: utf-8 -*-

from pathlib import Path

import yaml

from simmate.utilities import copy_directory
from simmate.workflow_engine import Workflow
from simmate.workflows.utilities import get_workflow


class Restart__Toolkit__Automatic(Workflow):
    """
    Given a directory of a incomplete Simmate workflow run, this will use the
    metadata file to restart the calculation.

    Example yaml file:

    ``` yaml
    workflow-name: restart.simmate.automatic
    directory_old: path/to/calc
    directory_new: path/to/newcalc (optional)
    ```

    No other inputs are allowed bc the simmate_metadata.yaml will be used.
    """

    @classmethod
    def run_config(cls, directory_old: Path, directory_new: Path = None, **kwargs):

        # First copy over the directory
        directory_new_cleaned = copy_directory(directory_old, directory_new)

        # grab the metadata file in the new dir
        metadata_filename = directory_new_cleaned / "simmate_metadata_01.yaml"
        with metadata_filename.open() as file:
            metadata = yaml.full_load(file)

        # Update the parameters from the metadata below
        input_parameters = metadata.copy()

        # remove settings that will be reset elsewhere
        input_parameters.pop("run_id", None)
        input_parameters.pop("directory", None)
        input_parameters.pop("copy_previous_directory", None)
        input_parameters.pop("is_restart", None)

        # grab the workflow we need to run
        workflow_name = input_parameters.pop("workflow_name")
        workflow = get_workflow(workflow_name)

        # update the source
        input_parameters.pop("source", None)
        input_parameters["source"] = {
            "database_table": workflow.database_table.table_name,
            "directory": directory_old,
            # BUG: I should force directory_old to be an absolute path in order
            # to store it here, but I'm unsure how to properly handle different
            # file systems...
            "is_restart": True,
        }

        # now instead of calling the workflow's run method, we use its run_restart
        state = workflow.run(
            directory=directory_new_cleaned,
            is_restart=True,
            **input_parameters,
        )
        result = state.result()

        return result
