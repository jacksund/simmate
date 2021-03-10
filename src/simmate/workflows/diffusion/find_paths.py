# -*- coding: utf-8 -*-

"""

ETL (Extract, Transform, Load)
E = load structure from sql database given id
T = run pymatgen-diffusion to find all pathways
L = add pathways to SQL database

Example of running the code below:
    structure_id = 1
    e = load_structure_from_db(structure_id)
    t = find_paths(e)
    l = add_paths_to_db(structure_id, t)

"""

from pymatgen_diffusion.neb.pathfinder import DistinctPathFinder

from prefect import Flow, Parameter, task
from prefect.storage import Local as LocalStorage

from simmate.configuration import django  # ensures setup
from simmate.database.diffusion import (
    MaterialsProjectStructure as MPS,
    Pathway as Pathway_DB,
)

# --------------------------------------------------------------------------------------


@task
def load_structure_from_db(structure_id):

    # grab the proper Structure entry and we want only the structure_json column
    structure_db = MPS.objects.only("structure_json").get(id=structure_id)

    # convert to a pymatgen object
    structure = structure_db.to_pymatgen()

    return structure


# --------------------------------------------------------------------------------------


@task
def find_paths(structure):

    # Make sure that "F" is in this structure. IF not, exit the function
    # !!! I think this check belongs in DistinctPathFinder
    if "F" not in structure.composition:
        return

    # Use pymatgen diffusion to identify all paths
    # TODO: I just hardcode my options here, but in the future, I can have this task
    # accept some kwargs to pass DistinctPathFinder
    dpf = DistinctPathFinder(
        structure=structure,
        migrating_specie="F",
        max_path_length=5,
        symprec=0.1,
        perc_mode=None,
    )

    # grab all the paths as MigrationPath objects
    paths = dpf.get_paths()

    return paths


# --------------------------------------------------------------------------------------


@task
def add_paths_to_db(structure_id, paths, path_limit=5):

    # make sure some pathways were actually provided. If not, exit the function.
    if not paths:
        return

    # iterate through the pathways and save them to the database
    # Note for the isite, msite, and esite storage:
    # " ".join(str(c) for c in coords) takes a numpy array and converts it to a
    # list with out brackets or commas. For example,
    # array([0.25, 0.13, 0.61]) --> '0.25 0.13 0.61'
    for path_index, path in enumerate(paths):
        # we only want to paths up to the pathlimit -- so don't do any more than that
        if path_index >= path_limit:
            break
        # convert the pathway object into the database table format
        pathway = Pathway_DB.from_pymatgen(path, structure_id)

        # TODO: make sure an idenitical path is not already in the database

        # save the new row to the database
        pathway.save()


# --------------------------------------------------------------------------------------


# now make the overall workflow
with Flow("Find Diffusion Pathways") as workflow:

    # load the structure object from our database
    structure_id = Parameter("structure_id")

    # load the structure object from our database
    structure = load_structure_from_db(structure_id)

    # identify all diffusion pathways for this structure
    pathways = find_paths(structure)

    # and the pathways to our database
    add_paths_to_db(structure_id, pathways)

# for Prefect Cloud compatibility, set the storage to a an import path
workflow.storage = LocalStorage(path=f"{__name__}:workflow", stored_as_script=True)

# --------------------------------------------------------------------------------------
