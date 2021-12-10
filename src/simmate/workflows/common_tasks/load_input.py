# -*- coding: utf-8 -*-

from django.utils.module_loading import import_string

from prefect import task

from pymatgen.core.structure import Structure

from simmate.website.local_calculations import models as all_datatables


# OPTIMIZE:
# Find a better place for this code. Maybe attach it the core structure class
# and have from_pymatgen, from_dict, from_database methods. And then a
# from_dynamic method that handles this input.

# Also consider splitting into load_structure and load_directory so that
# our flow_visualize looks cleaner


@task(nout=2)
def load_input(structure, directory=None, use_previous_directory=False):
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

    # if the input is already a pymatgen structure, just return it back
    if isinstance(structure, Structure):
        return structure, directory

    # otherwise we have a dictionary object

    # if the "@module" key is in the dictionary, then we have a pymatgen structure
    # dict which we convert to a pymatgen object and return
    if "@module" in structure.keys():
        return Structure.from_dict(structure), directory

    # otherwise we now know we have a dictionary pointing to the simmate database

    # first start by loading the datbase table, which is given as a module path
    datatable_str = structure["calculation_table"]

    # Import the datatable class -- how this is done depends on if it is from
    # a simmate supplied class or if the user supplied a full path to the class
    # OPTIMIZE: is there a better way to do this?
    if hasattr(all_datatables, datatable_str):
        datatable = getattr(all_datatables, datatable_str)
    else:
        datatable = import_string(datatable_str)

    # These attributes tells us which structure to grab from our datatable. The
    # user should have only provided one -- if they gave more, we just use whichever
    # one comes first.
    prefect_flow_run_id = structure.get("prefect_flow_run_id")
    calculation_id = structure.get("calculation_id")
    directory_old = structure.get("directory")

    # we must have either a prefect_flow_run_id or calculation_id
    if not prefect_flow_run_id and not calculation_id and not directory_old:
        raise Exception(
            "You must have either a prefect_flow_run_id, calculation_id, or directory"
            " provided if you want to load a structure from a previous calculation."
        )

    # now query the datable with which whichever was provided. Each of these
    # are unique so all three should return a single calculation.
    if calculation_id:
        calculation = datatable.objects.get(id=calculation_id)
    elif prefect_flow_run_id:
        calculation = datatable.objects.get(prefect_flow_run_id=prefect_flow_run_id)
    elif directory_old:
        calculation = datatable.objects.get(directory=directory_old)

    # In some cases, the structure we want is not within the calculation table.
    # For example, in relaxations the final structure is attached via table.structure_final
    structure_field = structure.get("structure_field")
    if structure_field:
        structure = getattr(calculation, structure_field).to_pymatgen()
    # if there's no structure field, that means we already have the correct entry
    else:
        structure = calculation.to_pymatgen()

    # if the user requested, we grab the previous directory as well
    if use_previous_directory:
        directory_new = calculation.directory
        # this check just makes sure we've been following logic correctly above.
        # It should never be hit
        if use_previous_directory and directory_old:
            assert directory_old == directory_new
    # Otherwise use the directory provided
    else:
        directory_new = directory

    # structure should now be a pymatgen structure object
    return structure, directory_new
