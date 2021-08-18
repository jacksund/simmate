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

# TODO: I should write an "update-database" function that uses MP's "last_updated"
# field. Then I could have a scheduled Prefect workflow that checks for updates
# daily/weekly. Alternatively, I could just download their entire database from
# scratch on a more extended schedule (say once per year). The extended schedule
# is easier to implement but won't stay current. Also using mpr.get_database_version()
# may be another helpful approach -- and we just update the entire database every
# time this changes by looking for where structure's "last_updated" changed.

# BUG: How should I handle when a structure is updated, but Simmate workflows had
# already been ran on past structures? Should I make a new entry in such cases? Or
# flag calculations as depreciated/outdated somehow?

# OPTIMIZE: Should I make this a Prefect workflow? The main reason I don't right
# now is because I'm not sure how to scatter data to all workers. Prefect cloud
# also crashes if I map this many structures into separate tasks. Since I'm just
# running this function once and always doing it locally, I just ignore ETL and
# don't use Prefect.

# OPTIMIZE: I don't use any parallelization here, but may want to consider Dask.

from django.db import transaction

from tqdm import tqdm
from pymatgen.ext.matproj import MPRester

from simmate.configuration.django import setup_full  # sets up database

from simmate.database.third_parties.materials_project import MaterialsProjectStructure
from simmate.database.third_parties.scraping.utilities import get_sanitized_structure

# --------------------------------------------------------------------------------------


@transaction.atomic
def load_all_structures(
    criteria={"task_id": {"$exists": True}},
    # !!! for testing
    # criteria={
    #     "task_id": {"$exists": True, "$in": ["mp-" + str(n) for n in range(1, 1000)]}
    # },
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
        "final_energy_per_atom",
        "formation_energy_per_atom",
        "e_above_hull",
        "structure",
        "band_gap",
    ]

    # now make the query and grab everything from the Materials Project!
    # the output dictionary is given back within a list, where each entry is
    # a specific structure (so a single mp-id)
    # Note: this is a very large query, so make sure your computer has enough
    # memory (RAM >10GB) and a stable internet connection.
    data = mpr.query(criteria, properties)

    # Let's sanitize all structures first. So iterate through each one in the list
    # This also takes a while, so we use a progress bar
    # BUG: We init and update tqdm separately beacuse it conflicts with MPRester's bar
    progress_bar = tqdm(total=len(data), position=0)
    for entry in data:

        # update the progress bar
        progress_bar.update(1)

        # make a copy of the entry because we are going to be changing things in-place
        entry_cleaned = entry.copy()

        # Grab the structure from the input data dictionary
        structure = entry["structure"]

        # Run symmetry analysis and sanitization on the pymatgen structure
        structure_sanitized = get_sanitized_structure(structure)

        # update the structure for the entry copy
        entry_cleaned.update({"structure": structure_sanitized})

        # For full compatibility with django, we need to rename the material_id
        # to just id. Also since I'm changing things in place, I need to make a
        # copy of the dict as well.
        entry_cleaned = entry.copy()
        entry_cleaned["id"] = entry_cleaned.pop("material_id")
        # We also do the same with with e_above_hull to energy_above_hull
        # the *1000 converts to meV
        e_hull = entry_cleaned.pop("e_above_hull")
        entry_cleaned["energy_above_hull"] = e_hull * 1000 if e_hull != None else None

        # now convert the entry to a database object
        structure_db = MaterialsProjectStructure.from_pymatgen(**entry_cleaned)

        # and save it to our database!
        structure_db.save()


# --------------------------------------------------------------------------------------
