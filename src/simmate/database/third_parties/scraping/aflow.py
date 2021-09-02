# -*- coding: utf-8 -*-

"""

This file is for pulling AFLOW data into the Simmate database. 

AFLOW's supported REST API can be accessed via "AFLUX API". This is a separate
python package, which is maintained at https://github.com/rosenbrockc/aflow.
Note that this not from the official AFLOW team, but it is made such that keywords
are pulled dynamically from the AFLOW servers -- any updates in AFLOW's API should
be properly handled. Also structures are loaded as ASE Atom objects, which we then
convert to pymatgen.

"""

from django.db import transaction

from tqdm import tqdm
from pymatgen.io.ase import AseAtomsAdaptor
from aflow import K as AflowKeywords
from aflow.control import Query as AflowQuery

from simmate.configuration.django import setup_full  # sets up database

from simmate.database.third_parties.aflow import AflowStructure
from simmate.utilities import get_sanitized_structure

# --------------------------------------------------------------------------------------


@transaction.atomic
def load_all_structures():

    # The way we build a query looks similar to the Django API, where we start
    # with a Query object (similar to Table.objects manager) and build filters
    # off of it.
    data = (
        AflowQuery(
            # This is a list of the supported "catalogs" that AFLOW has -- which appear
            # to be separately stored databases. I just use all of them by default.
            catalog=[
                "icsd",  # 60,000 structures
                "lib1",  # 4,000 structures
                "lib2",  # 360,000 structures (binary phases)
                "lib3",  # 2,530,000 structures (ternary phases)
            ],
            # The batch size the number of results to return per HTTP request.
            batch_size=500,
        )
        # .filter(
        #     # Now we want set the conditions for which structures to pull. Because we
        #     # want all of them, we normally comment this line out. For testing, we
        #     # can pull a smaller subset of the structures.
        #     # I use the element Dy because it gives about 1,300 structures
        #     AflowKeywords.species == "Dy",
        # )
        .select(
            # Indicate what data we want to grab from each result. Note that we don't
            # access the structure quite yet.
            AflowKeywords.auid,
            # This is the URL that leads to the rest of the data. Note it is a
            # interactive REST endpoint, while the dashboard link is different.
            # AflowKeywords.aurl,
            # The date that the entry was added
            # AflowKeywords.aflowlib_date,
            # Band gap
            AflowKeywords.Egap,
            # The calculated energy of the unit cell
            # BUG: how do we know energies are compatible?
            AflowKeywords.enthalpy_atom,
            AflowKeywords.enthalpy_cell,
            AflowKeywords.enthalpy_formation_atom,
        )
    )

    # Let's sanitize all structures first. So iterate through each one in the list
    # This also takes a while, so we use a progress bar (via tqdm)
    for entry in tqdm(data):

        # grab the structure -- this is loaded as an ASE atoms object
        structure_ase = entry.atoms()

        # convert the structure to pymatgen
        structure_pmg = AseAtomsAdaptor.get_structure(structure_ase)

        # Run symmetry analysis and sanitization on the pymatgen structure
        structure_sanitized = get_sanitized_structure(structure_pmg)

        # Compile all of our data into a dictionary
        entry_dict = {
            "structure": structure_sanitized,
            "id": entry.auid.replace(":", "-"),
            "final_energy": entry.enthalpy_cell,  # or is it energy_cell?
            "final_energy_per_atom": entry.enthalpy_atom,
            "formation_energy_per_atom": entry.enthalpy_formation_atom,
            "band_gap": entry.Egap,
        }

        # now convert the entry to a database object
        structure_db = AflowStructure.from_pymatgen(**entry_dict)

        # and save it to our database!
        structure_db.save()


# --------------------------------------------------------------------------------------
