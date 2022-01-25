# -*- coding: utf-8 -*-

"""

> :warning: This file is only for use by the Simmate team. Users should instead
access data via the load_remote_archive method.

This file is for pulling JARVIS data into the Simmate database. 

JARVIS has a python package "jarvis-tools" that let's us pull some of their
database dumps. For instructions on how to do this, they provided 
[this link](https://colab.research.google.com/github/knc6/jarvis-tools-notebooks/blob/master/jarvis-tools-notebooks/Get_JARVIS_DFT_final_structures_in_ASE_or_Pymatgen_format.ipynb)

Alternatively, we could manually download 
[their database json files](https://jarvis-materials-design.github.io/dbdocs/thedownloads/). We specifically look at the "3D-materials curated data".

"""

from django.db import transaction

from tqdm import tqdm
from simmate.toolkit import Structure

from simmate.database.third_parties import JarvisStructure


# Jarvis is not a dependency of simmate, so make sure you install it before using
# this module
try:
    from jarvis.db.figshare import data as jarvis_helper
except:
    raise ModuleNotFoundError(
        "You must install jarvis with `conda install -c conda-forge jarvis-tools`"
    )


@transaction.atomic
def load_all_structures():
    """
    Only use this function if you are part of the Simmate dev team!

    Loads all structures directly for the JARVIS database into the local
    Simmate database.
    """

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

        # now convert the entry to a database object
        structure_db = JarvisStructure.from_toolkit(
            id=entry["jid"].lower(),
            structure=structure,
            energy_above_hull=entry["ehull"] if entry["ehull"] != "na" else None,
        )

        # and save it to our database!
        structure_db.save()
