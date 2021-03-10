# -*- coding: utf-8 -*-

"""

ETL (Extract, Transform, Load)
E = load structures from a Materials Project query
T = santize structures
L = add structures to SQL database

Example of running the code below:
    e = load_structures_from_mp({"material_id": "mp-1234"})
    t = sanitize_structure.map(e)
    l = add_structure_from_materialsproject.map(t)

Note, the *.map() means I run this function for each output in "e". This makes
use of running things in parallel for speed and also if one structure fails,
the others can continue unaffected. Also note parallelization is only really
useful if you are using a Postgres backend instead of SQLite.

"""

from datetime import timedelta

from pymatgen import MPRester
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer

from prefect import Flow, Parameter, task
from prefect.storage import Local as LocalStorage

from simmate.configuration import django  # ensures setup
from simmate.database.diffusion import MaterialsProjectStructure as MPS

# --------------------------------------------------------------------------------------


@task
def load_structures_from_mp(criteria, api_key="2Tg7uUvaTAPHJQXl"):
    # TODO in production, I need to remove my API key. Move this to a config file.

    # Filtering criteria for which structures to look at in the Materials Project
    # Catagories such as 'elements' that we can filter off of are listed here:
    #       https://github.com/materialsproject/mapidoc
    # Conditions such as $in or $exists that we filter based on are listed here:
    #       https://docs.mongodb.com/manual/reference/operator/query/
    # As the simplest example, I only want one structure and I grab it by it's
    # mp-id in this code:
    # criteria = {"task_id": mp_id}

    # Connect with personal API key
    mpr = MPRester(api_key)

    # For reference, grab the database version
    db_version = mpr.get_database_version()
    print(f"You are currently using MP database version {db_version}")
    # '2020_09_08'
    # TODO: this isn't used at the moment, but I should implement a check in the future

    # For the filtered structures, which properties I want to grab.
    # All properties that we can grab are listed here:
    #       https://github.com/materialsproject/mapidoc
    # All of these properties listed are what I include in the main SQL table
    # see website.diffusion.models.Structure for the table schema
    properties = [
        "material_id",
        "final_energy",
        "final_energy_per_atom",
        "formation_energy_per_atom",
        "e_above_hull",
        "structure",
    ]

    # now make the query!
    data = mpr.query(criteria, properties)

    # the output dictionary is given back within a list, where each entry is
    # a specific structure (so a single mp-id)
    return data


# --------------------------------------------------------------------------------------


@task
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

    # update the structure
    data.update({"structure": structure})

    # return back the sanitized data
    return data


# --------------------------------------------------------------------------------------


@task(max_retries=3, retry_delay=timedelta(seconds=5))
def add_structure_from_materialsproject(data):

    # convert the dictionary to django orm
    structure_db = MPS.from_dict(data)

    # save the data to the database
    structure_db.save()


# --------------------------------------------------------------------------------------

# now make the overall workflow
with Flow("Add Structures from Materials Project") as workflow:

    # The input should be a Materials Project query dictionary
    criteria = Parameter("criteria")

    # load the materials data
    pulled_data = load_structures_from_mp(criteria)

    # cleanup the data
    cleaned_data = sanitize_structure.map(pulled_data)

    # and add it to our database
    add_structure_from_materialsproject.map(cleaned_data)


# for Prefect Cloud compatibility, set the storage to a an import path
workflow.storage = LocalStorage(path=f"{__name__}:workflow", stored_as_script=True)

from prefect.executors import DaskExecutor
workflow.executor = DaskExecutor(address="tcp://152.2.172.72:8786")

# --------------------------------------------------------------------------------------
