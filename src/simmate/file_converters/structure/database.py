# -*- coding: utf-8 -*-

"""
This module provides conversion between Simmate toolkit and database structures.

Everything is built-in to the base toolkit/database classes, so you typically 
convert between these two without ever loading this module directly.

Recommended use:
``` python
# using MatProj as an example, but the same applies for all Structure tables
from simmate.database.third_parties import MatProjStructure

db_structure = MatProjStructure.objects.first()

# convert to toolkit
tk_structure = db_structure.to_toolkit()

# convert back to database (as new row)
db_structure2 = MatProjStructure.from_toolkit(structure=structure)
```
"""

from django.utils.module_loading import import_string

from simmate.database import connect
from simmate.website.workflows import models as all_datatables
from simmate.toolkit import Structure as ToolkitStructure

# from simmate.database.base_data_types import Structure as DatabaseStructure


class DatabaseAdapter:
    """
    Adaptor for conversion between the Simmate ToolkitStructure object and
    Simmate DatabaseStructure object.
    """

    # It currently doesn't make sense to have this method, as it would
    # be converting to an abstract class. Perhaps (alternatively), this method
    # could search all tables and look for exact matches...?
    #
    # @staticmethod
    # def get_database(structure: ToolkitStructure) -> DatabaseStructure:
    #     return ...

    # This method is not included as it is obtuse and promotes improper use.
    # We keep this comment here for those inspecting the code for understanding.
    #
    # @staticmethod
    # def get_toolkit(structure: DatabaseStructure) -> ToolkitStructure:
    #     return structure.to_toolkit()

    @staticmethod
    def get_toolkit_from_database_dict(structure: dict) -> ToolkitStructure:
        """
        This is an experimental feature.

        Loads a structure from the Simmate database from a dictionary of
        metadata.
        """

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
            structure_cleaned = getattr(calculation, structure_field).to_toolkit()
        # if there's no structure field, that means we already have the correct entry
        else:
            structure_cleaned = calculation.to_toolkit()

        # For ease of access, we also link the calculation database entry
        structure_cleaned.calculation = calculation

        return structure_cleaned

    @staticmethod
    def get_toolkit_from_database_string(structure_string: str) -> ToolkitStructure:
        """
        Loads a toolkit structure from a string -- specifically strings that
        are stored in the structure_string column for
        simmate.database.base_data_types.Structure.
        """
        # Dev note: this method should be merged with the Toolkit.from_str method.
        # I only have this separate for now because pymatgen's from_str doesn't
        # dynamically determine format from the string alone.

        # convert the stored string to python dictionary.
        storage_format = "CIF" if (structure_string[0] == "#") else "POSCAR"
        # OPTIMIZE: see my comment on storing strings in the from_toolkit method above.
        # For now, I need to figure out if I used "CIF" or "POSCAR" and read the structure
        # accordingly. In the future, I can just assume my new format.
        # If the string starts with "#", then I know that I stored it as a "CIF".

        # convert the string to pymatgen Structure object
        if storage_format == "POSCAR":
            structure = ToolkitStructure.from_str(
                structure_string,
                fmt=storage_format,
            )

        # BUG: for cod structures we need to set the tolerance to "inf", which
        # isn't possible with the toolkit.from_str method. Instead we need to
        # call the CifParser directly
        elif storage_format == "CIF":
            from pymatgen.io.cif import CifParser

            parser = CifParser.from_string(
                structure_string,
                occupancy_tolerance=float("inf"),
            )
            structure = parser.get_structures()[0]

        return structure
