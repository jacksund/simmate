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

import json

from pymatgen.core.structure import Structure
from pymatgen_diffusion.neb.pathfinder import DistinctPathFinder

from prefect import Flow, Parameter, task

# --------------------------------------------------------------------------------------


@task
def load_structure_from_db(structure_id):

    from simmate.configuration import manage_django  # ensures setup
    from simmate.database.all import Structure as Structure_DB

    # grab the proper Structure entry and we want only the structure column
    # This query is ugly to read so here's the breakdown:
    #   .values_list("structure", flat=True) --> only grab the structure column
    #   .get(id=structure_id) --> grab the structure by row id (or personal key)
    #   ['structure'] --> the query gives us a dict where we just want this key's value
    structure_json = Structure_DB.objects.values_list(
        "structure",
        flat=True,
    ).get(id=structure_id)

    # convert the output from a json string to python dictionary
    structure_dict = json.loads(structure_json)
    # convert the output from a dictionary to pymatgen Structure object
    structure = Structure.from_dict(structure_dict)

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

    from simmate.configuration import manage_django  # ensures setup
    from simmate.database.all import Structure as Structure_DB, Pathway as Pathway_DB

    # make sure some pathways were actually provided. If not, exit the function.
    if not paths:
        return

    # grab the proper Structure entry
    # OPTIMIZE: will this function still work if I only grab the id value?
    structure = Structure_DB.objects.get(id=structure_id)

    # now iterate through the pathways and save them to the database
    # Note for the isite, msite, and esite storage:
    # " ".join(str(c) for c in coords) takes a numpy array and converts it to a
    # list with out brackets or commas. For example,
    # array([0.25, 0.13, 0.61]) --> '0.25 0.13 0.61'
    # To convert back, just use numpy.fromstring(string, , sep=' ') method
    for path_index, path in enumerate(paths):
        # we only want to paths up to the pathlimit -- so don't do any more than that
        if path_index >= path_limit:
            break
        # convert the pathway object into the database table format
        pathway = Pathway_DB(
            element="F",
            dpf_index=path_index,
            distance=path.length,
            isite=" ".join(str(c) for c in path.isite.frac_coords),
            msite=" ".join(str(c) for c in path.msite.frac_coords),
            esite=" ".join(str(c) for c in path.esite.frac_coords),
            structure=structure,
        )

        # TODO: make sure an idenitical path is not already in the database

        # save the new row to the database
        pathway.save()


# --------------------------------------------------------------------------------------


# now make the overall workflow
with Flow("Find_DiffusionPathways") as workflow:

    # load the structure object from our database
    structure_id = Parameter("structure_id")

    # load the structure object from our database
    structure = load_structure_from_db(structure_id)

    # identify all diffusion pathways for this structure
    pathways = find_paths(structure)

    # and the pathways to our database
    add_paths_to_db(structure_id, pathways)


# --------------------------------------------------------------------------------------
