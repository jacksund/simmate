# -*- coding: utf-8 -*-

"""

This file is for pulling OQMD data into the Simmate database. 

There are many ways to pull from this database, but it looks like the easiest
is the qmpy_rester python package. This officially supported and maintained
at https://github.com/mohanliu/qmpy_rester. For now the package is only available
via a pip install.

For other options such as the REST API, check out http://oqmd.org/static/docs/restful.html

"""

from django.db import transaction

from tqdm import tqdm
from pymatgen.core.structure import Structure
import qmpy_rester

from simmate.configuration.django import setup_full  # sets up database

from simmate.database.third_parties.oqmd import OqmdStructure
from simmate.utilities import get_sanitized_structure

# --------------------------------------------------------------------------------------


@transaction.atomic
def load_all_structures():

    # The documentation indicates that we handle a query via a context manager
    # for qmpy_rester. Each query is returned as a page of data, where we need
    # to iterate through all of the pages. To do this, we constantly make a query
    # and check the "next" field, which tells us if its the last page or not.

    # as we download all the data, we store it in a main list
    data = []

    # starting from the first page, assume we aren't on the last page until told
    # otherwise. And loop until we know its the last page.
    current_page = 0
    is_last_page = False
    while not is_last_page:

        # results per page is set based on OQMD recommendations and is constant (2000)
        # !!! for testing, try a smaller number like 100
        results_per_page = 100

        with qmpy_rester.QMPYRester() as query:

            # make the query
            result = query.get_oqmd_phases(
                verbose=False,
                limit=results_per_page,
                offset=current_page * results_per_page,
                #
                # Note delta_e is the formation energy and then stability is the
                # energy above hull.
                fields="entry_id,unit_cell,sites,delta_e,stability,band_gap",
                element_set="Al,C",  # !!! for testing
            )
            # grab the data for the next slice of structures
            query_slice = result["data"]
            # And check to see if this is the last page. The logic here is if
            # there is data for "next", then it isn't the last page
            is_last_page = not bool(result["links"]["next"])

            # store the slice of entrys in our main list
            for entry in query_slice:
                data.append(entry)

            # on the very first page, let's also check the total number of pages
            if current_page == 0:
                total_pages = result["meta"]["data_available"] // results_per_page

            # move on to the next page
            print(f"Successfully downloaded page {current_page} of {total_pages}")
            current_page += 1

    # Now iterate through all the data -- which is a list of dictionaries.
    # We convert the data into a pymatgen object and sanitize it before saving
    # to the Simmate database
    for entry in tqdm(data):

        # Parse the data into a pymatgen object
        # Also before converting into a pymatgen object, we need to parse the sites,
        # which are given as a list of "Element @ X Y Z" (for example "Na @ 0.5 0.5 0.5")
        # Changing this format is why we have this complex lists below
        structure = Structure(
            lattice=entry["unit_cell"],
            species=[site.split(" @ ")[0] for site in entry["sites"]],
            coords=[
                [float(n) for n in site.split(" @ ")[1].split()]
                for site in entry["sites"]
            ],
            coords_are_cartesian=False,
        )

        # Run symmetry analysis and sanitization on the pymatgen structure
        structure_sanitized = get_sanitized_structure(structure)

        # Compile all of our data into a dictionary
        entry_dict = {
            "structure": structure_sanitized,
            "id": "oqmd-" + str(entry["entry_id"]),
            # the *1000 converts to meV
            "energy_above_hull": entry["stability"] * 1000,
            "final_energy": entry["delta_e"],
            "band_gap": entry["band_gap"],
        }

        # now convert the entry to a database object
        structure_db = OqmdStructure.from_pymatgen(**entry_dict)

        # and save it to our database!
        structure_db.save()


# --------------------------------------------------------------------------------------
