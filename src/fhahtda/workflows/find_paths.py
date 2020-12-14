# -*- coding: utf-8 -*-

"""

NOTE: This currently only works with C:/Users/jacks/Documents/GitHub/fhahtda/website
as the working directory. I need to switch the database input parameter to a 
full path to fix this.

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

# --------------------------------------------------------------------------------------

import json
from pymatgen.core.structure import Structure
from prefect.tasks.database.sqlite import SQLiteQuery
from fhahtda.website.core.settings import DATABASES
db_filename = DATABASES["default"]["NAME"]

def load_structure_from_db(structure_id):

    # connect to the django database
    from fhahtda.website.manage import connect_db

    connect_db()

    # import the django models
    from fhahtda.database.all import Structure

    # grab the proper Structure entry and we want only the structure column
    structure_json = Structure.objects.get(id=structure_id).structure

    # convert the output from a json string to python dictionary
    structure_dict = json.loads(structure_json)
    # convert the output from a dictionary to pymatgen Structure object
    from pymatgen.core.structure import Structure
    structure = Structure.from_dict(structure_dict)

    return structure


def load_structure_from_db_FAST(structure_id, database=db_filename):

    # format the query using the data. This is the raw SQL command.
    # This command is the django equivalent of...
    # import manageinpython
    # from diffusion.models import Structure
    # structure = Structure.objects.get(id=structure_id).structure
    query = f"""
        SELECT diffusion_structure.structure 
        FROM diffusion_structure 
        WHERE diffusion_structure.id = {structure_id}
        """

    # Run the query using Prefect's code.
    #!!! In the future, just separate this into a separate step
    # I add the [0][0] because the output is returned within as [(structure)]
    structure_json = SQLiteQuery(database, query).run()[0][0]

    # convert the output from a json string to python dictionary
    structure_dict = json.loads(structure_json)
    # convert the output from a dictionary to pymatgen Structure object
    structure = Structure.from_dict(structure_dict)

    # out has no use here, but may contain error information
    return structure


# --------------------------------------------------------------------------------------


from pymatgen_diffusion.neb.pathfinder import DistinctPathFinder


def find_paths(structure):

    # Use pymatgen diffusion to identify all paths
    #!!! I just hardcode my options here, but in the future, I can have this task
    #!!! accept some kwargs to pass DistinctPathFinder
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


def add_paths_to_db(structure_id, paths):

    # paths are given a list of MigrationPath objects

    # connect to the django database
    from fhahtda.website.manage import connect_db

    connect_db()

    # import the django models
    from fhahtda.database.all import Structure, Pathway

    # grab the proper Structure entry
    structure = Structure.objects.get(id=structure_id)

    # now iterate through the pathways and save them to the database
    # Note for the isite, msite, and esite storage:
    # str(path.isite.frac_coords)[1:-1] takes a numpy array and converts it to a
    # list with out brackets or commas. For example,
    # array([0.25, 0.13, 0.61]) --> '0.25 0.13 0.61'
    # To convert back, just use numpy.fromstring(string, , sep=' ') method
    for path_index, path in enumerate(paths):
        pathway = Pathway(
            element="F",
            dpf_index=path_index,
            distance=path.length,
            isite=str(path.isite.frac_coords)[1:-1],
            msite=str(path.msite.frac_coords)[1:-1],
            esite=str(path.esite.frac_coords)[1:-1],
            structure=structure,
        )
        pathway.save()


def add_paths_to_db_FAST(structure_id, paths, database=db_filename):

    # paths are given a list of MigrationPath objects

    # format the query using the data. This is the raw SQL command.
    # we want to build our SQL command such that all pathways are added at once
    # therefore we build up the query string from scratch:
    query = """
        INSERT INTO diffusion_pathway
            (element, 
             dpf_index, 
             distance, 
             isite, 
             msite, 
             esite, 
             structure_id)
        VALUES
        """

    # now iterate through the paths and add the proper VALUE to the sql query
    for path_index, path in enumerate(paths):
        query += f"""
            ('F',
             {path_index},
             {path.length},
             '{str(path.isite.frac_coords)[1:-1]}',
             '{str(path.msite.frac_coords)[1:-1]}',
             '{str(path.esite.frac_coords)[1:-1]}',
             {structure_id}
             ),"""
    # finish off the list of insert VALUES with a semicolon and removing the last comma
    query = query[:-1] + ";"

    # Run the query using Prefect's code.
    #!!! In the future, just separate this into a separate step
    out = SQLiteQuery(database, query).run()

    # out has no use here, but may contain error information
    return out
