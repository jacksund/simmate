# -*- coding: utf-8 -*-

"""

This file is for pulling JARVIS data into the Simmate database. 

JARVIS has a python package "jarvis-tools" that let's us pull some of their
database dumps. For instructions on how to do this, they provided this link:
    https://colab.research.google.com/github/knc6/jarvis-tools-notebooks/blob/master/jarvis-tools-notebooks/Get_JARVIS_DFT_final_structures_in_ASE_or_Pymatgen_format.ipynb
    
Alternatively, we could manually download their database json files from here:
    https://jarvis-materials-design.github.io/dbdocs/thedownloads/
    >> looking at the "3D-materials curated data"

Currently we use the jarvis-tools package below. This is slow to download, but
at least saves us from manually finding the files.

"""

from django.db import transaction

from tqdm import tqdm
from pymatgen.core.structure import Structure

from jarvis.db.figshare import data as jarvis_helper

from simmate.configuration.django import setup_full  # sets up database

from simmate.database.third_parties.jarvis import JarvisStructure
from simmate.utilities import get_sanitized_structure

# --------------------------------------------------------------------------------------


@transaction.atomic
def load_all_structures(filename="jarvis.json"):

    # !!! Make sure you download the file, unzip it, and have it in your working
    # directory before loading this. Simply pick the most update file from here:
    # https://figshare.com/articles/dataset/jdft_3d-7-7-2018_json/6815699

    # Load all of the 3D data from JARVIS. This gives us a list of dictionaries
    # TODO: In the future, we can include other datasets like their 2D dataset.
    data = jarvis_helper("dft_3d")

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

        # Compile all of our data into a dictionary. If a value doesn't exist
        # for a given entry, JARVIS just uses "na" instead. We need to replace
        # these with None.
        entry_dict = {
            "structure": structure_sanitized,
            "id": entry["jid"].lower(),
            # the *1000 converts to meV
            "energy_above_hull": entry["ehull"] * 1000
            if entry["ehull"] != "na"
            else None,
            "formation_energy_per_atom": entry["formation_energy_peratom"]
            if entry["formation_energy_peratom"] != "na"
            else None,
        }

        # now convert the entry to a database object
        structure_db = JarvisStructure.from_pymatgen(**entry_dict)

        # and save it to our database!
        structure_db.save()


# --------------------------------------------------------------------------------------
