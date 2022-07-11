# -*- coding: utf-8 -*-

"""

> :warning: This file is only for use by the Simmate team. Users should instead
access data via the load_remote_archive method.

This file is for pulling Materials Project data into the Simmate database. 
PyMatGen offers an easy way to do this in python -- the MPRester class. All you
need is [an API key from their site](https://materialsproject.org/open) and pymatgen
installed. For now, we only pull the mp-id, structure, and final energy.

"""

from django.db import transaction

from tqdm import tqdm
from pymatgen.ext.matproj import MPRester

from simmate.database.third_parties import MatprojStructure


@transaction.atomic
def load_all_structures(
    api_key: str,
    criteria: dict = {"task_id": {"$exists": True}},
    update_stabilities: bool = False,
):
    """
    Only use this function if you are part of the Simmate dev team!

    Loads all structures directly for the Material Project database into the
    local Simmate database.

    #### Parameters

    - `api_key`:
        Your Materials Project API key.
    - `criteria`:
        Filtering criteria for which structures to load. The default is all
        existing structures (137,885 as of 2022-01-16), which will take rouhghly
        15 min to complete (not including stabilities).
    - `update_stabilities`:
        Whether to run update_all_stabilities on the database table. Note this
        will add over an hour to this process. Default is True.
    """

    # Notes on filtering criteria for structures in the Materials Project:
    #
    # Catagories such as 'elements' that we can filter off of are listed here:
    #       https://github.com/materialsproject/mapidoc
    # Conditions such as $in or $exists that we filter based on are listed here:
    #       https://docs.mongodb.com/manual/reference/operator/query/
    #
    # As the simplest example, I only want one structure and I grab it by it's
    # mp-id in this code:
    #   criteria = {"task_id": mp_id}
    #
    # Here, we want all structures! Which is why we use:
    #   criteria = {"task_id": {"$exists": True}}
    #
    # This is an alternative criteria input that can be used for testing
    # criteria={
    #     "task_id": {
    #         "$exists": True,
    #         "$in": ["mp-" + str(n) for n in range(1, 10000)]},
    # }
    #

    # Connect to their database with personal API key
    mpr = MPRester(api_key)

    # For the filtered structures, this lists off which properties to grab.
    # All possible properties are listed here:
    #       https://github.com/materialsproject/mapidoc
    properties = [
        "material_id",
        "final_energy",
        "structure",
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

        # convert the data to a Simmate database object
        structure_db = MatprojStructure.from_toolkit(
            id=entry["material_id"],
            structure=entry["structure"],
            energy=entry["final_energy"],
        )

        # and save it to our database!
        structure_db.save()

    # once all structures are saved, let's update the Thermodynamic columns
    if update_stabilities:
        MatprojStructure.update_all_stabilities()
