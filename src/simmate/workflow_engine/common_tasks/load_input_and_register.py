# -*- coding: utf-8 -*-

import os
import shutil
import yaml

import prefect
from prefect import Task

from simmate.utilities import get_directory
from simmate.toolkit import Structure
from simmate.database.base_data_types import DatabaseTable

from typing import Tuple, Any

# OPTIMIZE: consider splitting this task into load_structure, load_directory,
# and register_calc so that our flow_visualize looks cleaner


class LoadInputAndRegister(Task):
    def __init__(
        self,
        workflow_name: str = None,
        input_obj_name: str = None,
        calculation_table: DatabaseTable = None,
        **kwargs,
    ):
        self.workflow_name = workflow_name
        self.input_obj_name = input_obj_name
        self.calculation_table = calculation_table  # If None, registration is skipped
        super().__init__(**kwargs)

    def run(
        self,
        input_obj: Any,
        input_class: Any = Structure,
        source: dict = None,
        directory: str = None,
        copy_previous_directory: bool = False,
        **kwargs: Any,
    ) -> Tuple[Structure, str]:
        """
        How the input was submitted as a parameter depends on if we are submitting
        to Prefect Cloud, running the flow locally, or even continuing from a
        previous calculation.  Here, we use a task to convert the input to a toolkit
        object and (if requested) provide the directory as well.

        input_class is any class that has a from_dynamic method accepts the
        input_obj format. In the large majority of cases, this is just
        a Structure object so we use that as the default.

        directory is optional

        copy_previous_directory is only used when we are pulling a structure from a
        previous calculation. If copy_previous_directory=True, then the directory
        parameter is ignored.

        **kwargs is anything extra that you want saved to simmate_metadata.yaml
        """

        # -------------------------------------------------------------------------

        # First we load the structure to a toolkit structure object

        input_cleaned = input_class.from_dynamic(input_obj)

        # -------------------------------------------------------------------------

        # Now let's load the directory

        # Start by creating a new directory or grabbing the one given. We create
        # this directly immediately (rather than just passing the name to the
        # S3Task). We do this because NestedWorkflows often use a parent directory
        # to organize results.
        directory_cleaned = get_directory(directory)

        # if the user requested, we grab the previous directory as well
        if copy_previous_directory:

            # catch incorrect use of this function
            if not input_cleaned.is_from_past_calc:
                raise Exception(
                    "There isn't a previous directory available! Your source "
                    "structure must point to a past calculation to use this feature."
                )

            # the past directory should be stored on the input object
            previous_directory = input_cleaned.calculation.directory

            # First check if the previous directory exists. There are several
            # possibilities that we need to check for:
            #   1. directory exists on the same file system and can be found
            #   2. directory exists on the same file system but is now an archive
            #   3. directory/archive is on another file system (requires ssh to access)
            #   4. directory was deleted and unavailable
            # When copying over the directory, we ignore any `simmate_` files
            # that correspond to metadata/results/corrections/etc.
            if os.path.exists(previous_directory):
                # copy the old directory to the new one
                shutil.copytree(
                    src=previous_directory,
                    dst=directory_cleaned,
                    ignore=shutil.ignore_patterns("simmate_*"),
                    dirs_exist_ok=True,
                )
            elif os.path.exists(f"{previous_directory}.zip"):
                # unpack the old archive
                shutil.unpack_archive(
                    filename=f"{previous_directory}.zip",
                    extract_dir=os.path.dirname(previous_directory),
                )
                # copy the old directory to the new one
                shutil.copytree(
                    src=previous_directory,
                    dst=directory_cleaned,
                    ignore=shutil.ignore_patterns("simmate_*"),
                    dirs_exist_ok=True,
                )
                # Then remove the unpacked archive now that we copied it.
                # This leaves the original archive behind and unaltered too.
                shutil.rmtree(previous_directory)
            else:
                raise Exception(
                    "Unable to locate the previous calculation to copy. Make sure the "
                    "past directory is located on the same file system. Directory that "
                    f"couldn't be found was... {previous_directory}"
                )
            # TODO: for possibility 3, I could implement automatic copying with
            # the "fabric" python package (uses ssh). I'd also need to store
            # filesystem names (e.g. "WarWulf") to know where to connect.

        # -------------------------------------------------------------------------

        # Load the source of the input object

        # If we were given a input from a previous calculation, the source should
        # point directory to that same input. Otherwise we are incorrectly trying
        # to change what the source is.
        if source and input_cleaned.is_from_past_calc:
            # note input_obj here is a dictionary
            assert source == input_obj
        elif input_cleaned.is_from_past_calc:
            source_cleaned = input_obj
        elif source:
            source_cleaned = source
        else:
            source_cleaned = None

        # -------------------------------------------------------------------------

        # Register the calculation so the user can follow along in the UI.

        # This is only done if a table is provided. Some special-case workflows
        # don't store calculation information bc the flow is just a quick python
        # analysis.
        prefect_flow_run_id = prefect.context.flow_run_id
        if self.calculation_table:
            # load/create the calculation for this workflow run
            calculation = self.calculation_table.from_prefect_id(
                id=prefect_flow_run_id,
                # We pass the initial input_obj in case the calculation wasn't created
                # yet (and creation requires the structure)
                structure=input_cleaned,
                # BUG: what if the initial structure changed? An example of this happening
                # is with a relaxation where a correction was applied and the calc
                # was not fully restarted. This issue also will not matter when
                # workflows are ran through cloud -- as the structure is already
                # saved and won't be overwritten here.
                source=source_cleaned,
            )

        # -------------------------------------------------------------------------

        # Lastly, we want to write a file summarizing the inputs used for this
        # workflow run. This allows future users to reproduce the results if
        # desired -- and it also allows us to load old results into a database.
        input_summary = dict(
            workflow_name=self.workflow_name,
            source=source_cleaned,
            directory=directory_cleaned,
            # this ID is ingored as an input but needed for loading past data
            prefect_flow_run_id=prefect_flow_run_id,
            **kwargs,
        )
        # As a final thing to add, we want the input_obj, but we want to save
        # this to the proper input name. Also, this input should either be a
        # dictionary or a python object, where we convert to a dictionary in
        # order to write to file.
        input_dict = input_obj if isinstance(input_obj, dict) else input_obj.as_dict()
        input_summary[self.input_obj_name] = input_dict

        # now write the summary to file in the same directory as the calc.
        input_summary_filename = os.path.join(
            directory_cleaned, "simmate_metadata.yaml"
        )
        with open(input_summary_filename, "w") as file:
            content = yaml.dump(input_summary)
            file.write(content)

        # -------------------------------------------------------------------------

        # the rest of the calculation doesn't need the source (that was only for
        # registering the calc), so we just return the pymatgen structure and dir
        return input_cleaned, directory_cleaned
