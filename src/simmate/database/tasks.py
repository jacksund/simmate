# -*- coding: utf-8 -*-

import json

from pymatgen.core.structure import Structure
from pymatgen_diffusion.neb.pathfinder import DistinctPathFinder

from prefect import Flow, Parameter, task

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
