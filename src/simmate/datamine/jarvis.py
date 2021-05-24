# -*- coding: utf-8 -*-

"""

This file is for pulling JARVIS data into the Simmate database. 

It's unclear how JARVIS prefers uses to access their data, as they have a python
package and REST API, but poor documentation on how to pull from their database.
What looks like the most straight-forward is their downloads section:
    https://jarvis-materials-design.github.io/dbdocs/thedownloads/
    >> looking at the "3D-materials curated data"
This is really just a large JSON file that I can download manually, and then
add to the database using this script. The JSON of the metadata includes the structure
information, which we need to format/feed into a pymatgen object.

"""

import json

from django.db import transaction

from tqdm import tqdm
from pymatgen.core.structure import Structure

from simmate.configuration.django import setup_full  # sets up database

# from simmate.database.third_parties.aflow import JarvisStructure
from simmate.datamine.utilities import get_sanitized_structure

# --------------------------------------------------------------------------------------


@transaction.atomic
def load_all_structures(filename="jarvis.json"):

    # !!! Make sure you download the file, unzip it, and have it in your working
    # directory before loading this. Simply pick the most update file from here:
    # https://figshare.com/articles/dataset/jdft_3d-7-7-2018_json/6815699

    # load the entire json file into python and close the file right away
    with open(filename) as file:
        data = json.load(file)

    # Now iterate through all the data -- which is a list of dictionaries.
    # We convert the data into a pymatgen object and sanitize it before saving
    # to the Simmate database
    for entry in tqdm(data):

        # The structure is in the atoms field as a dictionary. We pull this data
        # out and convert it to a pymatgen Structure object
        structure = Structure(
            lattice=entry["atoms"]["lattice_mat"],
            species=entry["atoms"]["elements"],
            coords=entry["atoms"]["coords"],
            coords_are_cartesian=entry["atoms"]["cartesian"],
        )

        # Run symmetry analysis and sanitization on the pymatgen structure
        structure_sanitized = get_sanitized_structure(structure)

        # Compile all of our data into a dictionary
        entry_dict = {
            "structure": structure_sanitized,
            "jid": entry["jid"],
            "ehull": entry["ehull"],
            "formation_energy_peratom": entry["formation_energy_peratom"],
            "xml_data_link": entry["xml_data_link"],
        }

        # now convert the entry to a database object
        # structure_db = JarivsStructure.from_dict(entry_dict)

        # and save it to our database!
        # structure_db.save()


# --------------------------------------------------------------------------------------
