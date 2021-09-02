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

from tqdm import tqdm

from django.db import transaction

# This looks like the easiest way to grab all of the data -- as AFLOW doesn't
# have any good documentation on doing this.
from pymatgen.analysis.prototypes import AFLOW_PROTOTYPE_LIBRARY

from simmate.configuration.django import setup_full  # sets up database

from simmate.database.prototypes.aflow import AflowPrototype
from simmate.utilities import get_sanitized_structure


@transaction.atomic
def load_all_prototypes():

    for prototype_data in tqdm(AFLOW_PROTOTYPE_LIBRARY):

        # first let's grab the structure and sanitize it
        structure = prototype_data["snl"].structure
        structure_sanitized = get_sanitized_structure(structure)

        # Organize the data into our database format
        prototype = AflowPrototype.from_pymatgen(
            structure=structure_sanitized,
            mineral_name=prototype_data["tags"]["mineral"],
            aflow_id=prototype_data["tags"]["aflow"],
            pearson_symbol=prototype_data["tags"]["pearson"],
            strukturbericht=prototype_data["tags"]["strukturbericht"],
        )

        # and save it to our database
        prototype.save()
