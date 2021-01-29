# -*- coding: utf-8 -*-

"""

ETL (Extract, Transform, Load)
E = load structure from mp, file, dict, etc. (in this project, I only do mp)
T = santize structure
L = add structure to SQL database

Example of running the code below:
    e = load_structure_from_mp('mp-8226')
    t = sanitize_structure(e)
    l = add_structure_from_mp(t)

"""

from pymatgen import MPRester
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer

from simmate.configuration import manage_django  # ensures setup
from simmate.database.all import Structure as Structure_DB

# --------------------------------------------------------------------------------------


def load_structure_from_mp(mp_id, api_key="2Tg7uUvaTAPHJQXl"):
    # TODO in production, I need to remove my API key. Move this to a config file.

    # Connect with personal API key
    mpr = MPRester(api_key)

    # For reference, grab the database version
    db_version = mpr.get_database_version()
    print(f"You are currently using MP database version {db_version}")
    # '2020_09_08'
    # TODO: this isn't used at the moment, but I should implement a check in the future

    # Filtering criteria for which structures to look at in the Materials Project
    # Catagories such as 'elements' that we can filter off of are listed here:
    #       https://github.com/materialsproject/mapidoc
    # Conditions such as $in or $exists that we filter based on are listed here:
    #       https://docs.mongodb.com/manual/reference/operator/query/
    # Here, I only want one structure and I grab it by it's mp-id.
    criteria = {"task_id": mp_id}

    # For the filtered structures, which properties I want to grab.
    # All properties that we can grab are listed here:
    #       https://github.com/materialsproject/mapidoc
    # All of these properties listed are what I include in the main SQL table
    # see website.diffusion.models.Structure for the table schema
    properties = [
        "material_id",
        "nsites",
        "pretty_formula",
        "final_energy",
        "final_energy_per_atom",
        "formation_energy_per_atom",
        "e_above_hull",
        "density",
        "structure",
    ]

    # now make the query!
    data = mpr.query(criteria, properties)

    # the output dictionary is given back within a list. Just pull it out of the list
    # and return the result
    return data[0]


# --------------------------------------------------------------------------------------


def sanitize_structure(data):
    # TODO: Data is the output dict of load_structure_from_mp. In the future, switch the
    # input to only be a pymatgen Structure object.

    # make a copy of data because we are going to be changing things in-place
    data = data.copy()

    # Grab the structure from the input data dictionary
    structure = data["structure"]

    # Run symmetry and "sanitization" on the pymatgen structure

    # Make sure we have the primitive unitcell first
    # We choose to use SpagegroupAnalyzer (which uses spglib) rather than pymatgen's
    # built-in Structure.get_primitive_structure function:
    #   structure = structure.get_primitive_structure(0.1) # Default tol is 0.25

    # Default tol is 0.01, but we use a looser 0.1 Angstroms
    structure = SpacegroupAnalyzer(structure, 0.1).find_primitive()

    # Convert the structure to a "sanitized" version.
    # This includes...
    #   (i) an LLL reduction
    #   (ii) transforming all coords to within the unitcell
    #   (iii) sorting elements by electronegativity
    structure = structure.copy(sanitize=True)

    # number of sites may have decreased when we switched to the primitive structure
    # so we need to update the value here
    data.update({"nsites": structure.num_sites})

    # update the structure
    data.update({"structure": structure})

    # return back the sanitized data
    return data


# --------------------------------------------------------------------------------------


def add_structure_from_mp(data):

    # make a copy of data because we are going to be changing things in-place
    data = data.copy()

    # convert the structure from pymatgen object to json string
    structure_json = data["structure"].to_json()

    # update the data dictionary
    data.update({"structure": structure_json})

    # initialize it using the data
    structure = Structure_DB(**data)

    # save the data to the database
    structure.save()


# --------------------------------------------------------------------------------------
