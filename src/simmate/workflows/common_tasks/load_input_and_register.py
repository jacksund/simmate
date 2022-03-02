# -*- coding: utf-8 -*-

import os
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
        use_previous_directory: bool = False,
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

        use_previous_directory is only used when we are pulling a structure from a
        previous calculation. If use_previous_directory=True, then the directory
        parameter is ignored.

        **kwargs is anything extra that you want saved to simmate_input.yaml
        """

        # -------------------------------------------------------------------------

        # First we load the structure to a toolkit structure object

        input_cleaned = input_class.from_dynamic(input_obj)

        # -------------------------------------------------------------------------

        # Now let's load the directory

        # if the user requested, we grab the previous directory as well
        if use_previous_directory and input_cleaned.is_from_past_calc:
            # this variable will only be set if the above conditions are met. In
            # this case we can grab the directory name for the simmate database entry
            directory_cleaned = input_cleaned.calculation.directory

        # catch incorrect use of this function
        elif use_previous_directory and not input_cleaned.is_from_past_calc:
            raise Exception(
                "There isn't a previous directory available! Your source structure "
                "must point to a past calculation to use this feature."
            )

        # otherwise use the directory that was given. We create this directly
        # immediately (rather than just passing the name to the S3Task). We
        # do this because NestedWorkflows often use a parent directory to
        # organize results.
        else:
            directory_cleaned = get_directory(directory)

        # This guards against incorrect use of the function too. We don't want
        # users asking to use a previous directory while also giving a brand
        # new directory.
        if use_previous_directory and directory:
            assert directory_cleaned == directory

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
