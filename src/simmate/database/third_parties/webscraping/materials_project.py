# -*- coding: utf-8 -*-

"""

This file is for pulling Materials Project data into the Simmate database. 
PyMatGen offers an easy way to do this in python -- the MPRester class. All you
need is an API key from https://materialsproject.org/open and pymatgen installed.
For now, we only pull the mp-id, structure, final energy, and energy above hull.

Note, that the structures we pull into our database may not be exact matches to
what's shown in their database. This is beacuse we run symmetry analysis on the
structure and convert to a LLL reduced cell.

"""

from django.db import transaction

from tqdm import tqdm
from pymatgen.ext.matproj import MPRester

from simmate.configuration.django import setup_full  # sets up database

from simmate.database.third_parties.materials_project import MaterialsProjectStructure


@transaction.atomic
def load_all_structures(
    # criteria={"task_id": {"$exists": True}},
    # !!! for testing
    criteria={
        "task_id": {"$exists": True, "$in": ["mp-" + str(n) for n in range(1, 1000)]},
    },
    api_key="2Tg7uUvaTAPHJQXl",  # TODO remove in production - maybe to a config file
):

    # We save a lot of structures to the database here, but we don't want to make an
    # new database call each time we save. That could overload our server and cause
    # it to crash. Instead, the "@transaction.atomic" let's us save all structures in
    # just one call to the database.

    # Filtering criteria for which structures to look at in the Materials Project
    # Catagories such as 'elements' that we can filter off of are listed here:
    #       https://github.com/materialsproject/mapidoc
    # Conditions such as $in or $exists that we filter based on are listed here:
    #       https://docs.mongodb.com/manual/reference/operator/query/
    # As the simplest example, I only want one structure and I grab it by it's
    # mp-id in this code:
    #   criteria = {"task_id": mp_id}
    # Here, we want all structures! Which is why we use:
    #   criteria = {"task_id": {"$exists": True}}

    # Connect to their database with my personal API key
    mpr = MPRester(api_key)

    # For the filtered structures, which properties I want to grab.
    # All properties that we can grab are listed here:
    #       https://github.com/materialsproject/mapidoc
    # All of these properties listed are what I include in the main SQL table
    # see website.diffusion.models.Structure for the table schema
    properties = [
        "material_id",
        "final_energy",
        "structure",
        # "bandstructure",
        # "bandstructure_uniform",
    ]

    # now make the query and grab everything from the Materials Project!
    # the output dictionary is given back within a list, where each entry is
    # a specific structure (so a single mp-id)
    # Note: this is a very large query, so make sure your computer has enough
    # memory (RAM >10GB) and a stable internet connection.
    data = mpr.query(criteria, properties)

    # Let's iterate through each structure and save it to the database
    # This also takes a while, so we use a progress bar
    # BUG: We init and update tqdm separately beacuse it conflicts with MPRester's bar
    progress_bar = tqdm(total=len(data), position=0)
    for entry in data:

        # update the progress bar
        progress_bar.update(1)

        # TODO:
        # bs = mpr.get_bandstructure_by_material_id("mp-323")

        structure_db = MaterialsProjectStructure.from_pymatgen(
            id=entry["material_id"],
            structure=entry["structure"],
            energy=entry["final_energy"],
        )

        # and save it to our database!
        structure_db.save()
