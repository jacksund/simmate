# -*- coding: utf-8 -*-

"""
This module defines the Structure class.

It is a very basic extension PyMatGen's core Structure class, as it only adds
a few extra methods and does not change any other usage.
"""

from pymatgen.core import Structure as PymatgenStructure


class Structure(PymatgenStructure):
    # Leave docstring blank and just inherit from pymatgen

    def get_sanitized_structure(self):
        """
        Run symmetry analysis and "sanitization" on the pymatgen structure
        """

        # Make sure we have the primitive unitcell first
        # We choose to use SpagegroupAnalyzer (which uses spglib) rather than pymatgen's
        # built-in Structure.get_primitive_structure function:
        #   structure = structure.get_primitive_structure(0.1) # Default tol is 0.25

        # Default tol is 0.01, but we use a looser 0.1 Angstroms
        # from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
        # structure_primitive = SpacegroupAnalyzer(structure, 0.1).find_primitive()
        # BUG: with some COD structures, this symm analysis doesn't work. I need
        # to look into this more and figure out why.

        # Default tol is 0.25 Angstroms
        structure_primitive = self.get_primitive_structure()

        # Convert the structure to a "sanitized" version.
        # This includes...
        #   (i) an LLL reduction
        #   (ii) transforming all coords to within the unitcell
        #   (iii) sorting elements by electronegativity
        structure_sanitized = structure_primitive.copy(sanitize=True)

        # return back the sanitized structure
        return structure_sanitized

    @classmethod
    def from_dynamic(cls, structure):
        """
        This is an experimental feature.

        Possible structure formats include...
            object of toolkit structure
            dictionary of toolkit structure
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
        """

        # keep track of this flag too, which we use in the next sections on loading
        # the directory and source
        is_from_past_calc = False

        # if the input is already a pymatgen structure, just return it back
        if isinstance(structure, PymatgenStructure):
            structure_cleaned = structure

        # if the "@module" key is in the dictionary, then we have a pymatgen
        # structure dict which we convert to a pymatgen object and return
        elif isinstance(structure, dict) and "@module" in structure.keys():
            structure_cleaned = cls.from_dict(structure)

        # if there is a calculation_table key, then we are pointing to the simmate
        # database for the input structure
        elif isinstance(structure, dict) and "calculation_table" in structure.keys():
            is_from_past_calc = True
            structure_cleaned = cls.from_database(structure)

        # Otherwise an incorrect format was given
        else:
            raise Exception(
                "Unknown format provided for structure input. "
                f"{type(structure)} was provided."
            )

        # add this attribute to help with error checking in other methods
        structure_cleaned.is_from_past_calc = is_from_past_calc

        return structure_cleaned

    @classmethod
    def from_database(cls, structure: dict):
        """
        This is an experimental feature.

        Loads a structure from the Simmate database.
        """

        # because the structure is in the databse, we need to setup django and
        # make sure we can access the tables
        from simmate.configuration.django import setup_full
        from simmate.website.local_calculations import models as all_datatables
        from django.utils.module_loading import import_string

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

    @classmethod
    def from_database_string(cls, structure_string: str):
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
            structure = cls.from_str(
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
