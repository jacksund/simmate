# -*- coding: utf-8 -*-

from django.utils.module_loading import import_string

import prefect
from prefect import Task

from pymatgen.core.structure import Structure

from simmate.website.local_calculations import models as all_datatables

from typing import Tuple

# OPTIMIZE:
# Find a better place for this code. Maybe attach it the core structure class
# and have from_pymatgen, from_dict, from_database methods. And then a
# from_dynamic method that handles this input.

# Also consider splitting into load_structure, load_directory, and register_calc
# so that our flow_visualize looks cleaner


class LoadInputAndRegister(Task):
    def __init__(self, calculation_table, **kwargs):
        self.calculation_table = calculation_table
        super().__init__(**kwargs)

    def run(
        self,
        structure: Structure,
        source: dict = None,
        directory: str = None,
        use_previous_directory: bool = False,
    ) -> Tuple[Structure, str]:
        """
        How the structure was submitted as a parameter depends on if we are submitting
        to Prefect Cloud, running the flow locally, or even continuing from a
        previous calculation.  Here, we use a task to convert the input to a pymatgen
        structure and (if requested) provide the directory as well.

        Possible structure formats include...
            object of pymatgen structure
            dictionary of pymatgen structure
            dictionary of...
                (1) python path to calculation datatable
                (2) one of the following (only one is used in this priority order):
                    (a) prefect flow id
                    (b) calculation id
                    (c) directory
                    ** these three are chosen because all three are unique for every
                    single calculation and we have access to different ones at different
                    times!
                (3) (optional) attribute to use on table (e.g. structure_final)
                    By default, we assume calculation table is also a structure table
            filename for a structure (cif, poscar, etc.) [TODO]

        directory is optional

        use_previous_directory is only used when we are pulling a structure from a
        previous calculation. If use_previous_directory=True, then the directory
        parameter is ignored.

        """

        # -------------------------------------------------------------------------

        # First we load the structure to a pymatgen object

        # keep track of this flag too, which we use in the next sections on loading
        # the directory and source
        is_structure_from_past_calc = False

        # if the input is already a pymatgen structure, just return it back
        if isinstance(structure, Structure):
            structure_cleaned = structure

        # if the "@module" key is in the dictionary, then we have a pymatgen
        # structure dict which we convert to a pymatgen object and return
        elif isinstance(structure, dict) and "@module" in structure.keys():
            structure_cleaned = Structure.from_dict(structure)

        # if there is a calculation_table key, then we are pointing to the simmate
        # database for the input structure
        elif isinstance(structure, dict) and "calculation_table":

            is_structure_from_past_calc = True

            # start by loading the datbase table, which is given as a module path
            datatable_str = structure["calculation_table"]

            # Import the datatable class -- how this is done depends on if it
            # is from a simmate supplied class or if the user supplied a full
            # path to the class
            # OPTIMIZE: is there a better way to do this?
            if hasattr(all_datatables, datatable_str):
                datatable = getattr(all_datatables, datatable_str)
            else:
                datatable = import_string(datatable_str)

            # These attributes tells us which structure to grab from our datatable.
            # The user should have only provided one -- if they gave more, we just
            # use whichever one comes first.
            prefect_flow_run_id = structure.get("prefect_flow_run_id")
            calculation_id = structure.get("calculation_id")
            directory_old = structure.get("directory")

            # we must have either a prefect_flow_run_id or calculation_id
            if not prefect_flow_run_id and not calculation_id and not directory_old:
                raise Exception(
                    "You must have either a prefect_flow_run_id, calculation_id, "
                    "or directory provided if you want to load a structure from "
                    "a previous calculation."
                )

            # now query the datable with which whichever was provided. Each of these
            # are unique so all three should return a single calculation.
            if calculation_id:
                calculation = datatable.objects.get(id=calculation_id)
            elif prefect_flow_run_id:
                calculation = datatable.objects.get(
                    prefect_flow_run_id=prefect_flow_run_id,
                )
            elif directory_old:
                calculation = datatable.objects.get(directory=directory_old)

            # In some cases, the structure we want is not within the calculation table.
            # For example, in relaxations the final structure is attached via
            # the table.structure_final attribute
            structure_field = structure.get("structure_field")
            if structure_field:
                structure_cleaned = getattr(calculation, structure_field).to_pymatgen()
            # if there's no structure field, that means we already have the correct entry
            else:
                structure_cleaned = calculation.to_pymatgen()

        # Otherwise an incorrect format was given
        else:
            raise Exception("Unknown format provided for structure input.")

        # -------------------------------------------------------------------------

        # Now let's load the directory

        # if the user requested, we grab the previous directory as well
        if use_previous_directory and is_structure_from_past_calc:
            # this variable will only be set if the above conditions are met. In
            # this case we can grab the directory name for the simmate database entry
            directory_cleaned = calculation.directory

        # catch incorrect use of this function
        elif use_previous_directory and not is_structure_from_past_calc:
            raise Exception(
                "There isn't a previous directory available! Your source structure "
                "must point to a past calculation to use this feature."
            )

        # otherwise use the directory that was given
        else:
            directory_cleaned = directory

        # This guards against incorrect use of the function too. We don't want
        # users asking to use a previous directory while also giving a brand
        # new directory.
        if use_previous_directory and directory:
            assert directory_cleaned == directory

        # -------------------------------------------------------------------------

        # Load the source of the structure

        # If we were given a structure from a previous calculation, the source should
        # point directory to that same structure. Otherwise we are incorrectly trying
        # to change what the source is.
        if source and is_structure_from_past_calc:
            # note structure here is a dictionary input
            assert source == structure
        elif is_structure_from_past_calc:
            source_cleaned = structure
        elif source:
            source_cleaned = source
        else:
            source_cleaned = None

        # -------------------------------------------------------------------------

        # Register the calculation so the user can follow along in the UI.

        # load/create the calculation for this workflow run
        calculation = self.calculation_table.from_prefect_id(
            prefect.context.flow_run_id,
            # We pass the initial structure in case the calculation wasn't created
            # yet (and creation requires the structure)
            structure=structure_cleaned,
            # BUG: what if the initial structure changed? An example of this happening
            # is with a relaxation where a correction was applied and the calc
            # was not fully restarted. This issue also will not matter when
            # workflows are ran through cloud -- as the structure is already
            # saved and won't be overwritten here.
            source=source_cleaned,
        )

        # -------------------------------------------------------------------------

        # the rest of the calculation doesn't need the source (that was only for
        # registering the calc), so we just return the pymatgen structure and dir
        return structure_cleaned, directory_cleaned


# These are my notes how we can specify a source
"""

method

table
    either Calculation, Structure table, or a table that is both
    if not Structure table:
        structure_field



if transformation and transformation.ninput > 1:
    one of the following:
        ids
        prefect_flow_ids
        directories
else:
    one of the following:
        id
        prefect_flow_id # only if Calculation table
        directory  # only if Calculation table



EXAMPLES...

# from a thirdparty database
source = {
    "table": "MaterialsProjectStructure",
    "id": "mp-123",
}

# from a random structure creator
source = {"method": "PyXtalStructure"}

# from a templated structure creator (e.g. substituition or prototypes)
source = {
    "method": "PrototypeStructure",
    "table": "AFLOWPrototypes",
    "id": 123,
}
source = {
    "method": "SubstituitionStructure",
    "table": "MaterialsProjectStructure",
    "id": "mp-123",
}

# from a transformation
source = {
    "method": "MirrorMutation",
    "table": "MaterialsProjectStructure",
    "id": "mp-123",
}

"""
