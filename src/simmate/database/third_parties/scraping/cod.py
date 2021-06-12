# -*- coding: utf-8 -*-


"""

This file is for pulling COD data into the Simmate database. 

The COD let's you download all of their data as a zip file. While they do have a
REST API, it looks like they prefer you to use the zip file if you want all structures
and metadata. This is a big download even when compressed (17GB), so it's a slow
process -- but more importantly a stable one. For future reference though, the REST
API is outlined here: https://wiki.crystallography.net/RESTful_API/

Once downloaded, all of the cif files are organized into folders based on their first
few numbers -- for example, the cif 1234567 would be in folder /cif/1/23/45/1234567.cif
It's an odd way of storing the files, but we just need to script opening all of the folders
open. Note that some folders also don't have any cifs in them! There is also extra data
in each cif file -- such as the doi of the paper it came from.

There looks to be a lot of problematic cif files in the COD, but it's not worth parsing
through all of these. Instead, I simply try to load the cif file into a pymatgen
Structure object, and if it fails, I just move on. I'm slowly adding functionality
to account for these problematic cif files though.

"""

import os

from django.db import transaction

from tqdm import tqdm
from pymatgen.io.cif import CifParser

from simmate.configuration.django import setup_full  # sets up database

from simmate.database.third_parties.cod import CodStructure
from simmate.database.third_parties.scraping.utilities import get_sanitized_structure

# --------------------------------------------------------------------------------------


@transaction.atomic
def load_all_structures(base_directory="cod/cif_testing/"):

    # We need to look at all the folders that have numbered-names (1,2,3..,9). and
    # grab the folder inside that are also numbers. This continues until we find cif
    # files that we can pull structures from. Note the name of the cif file is also
    # the cod-id.
    # We also use tqdm to monitor progress.
    for folder_name1 in tqdm(os.listdir(base_directory)):

        # skip if the folder name isn't a number
        if not folder_name1.isnumeric():
            continue

        # otherwise go through the folders inside of this one
        for folder_name2 in os.listdir(os.path.join(base_directory, folder_name1)):
            # and then one more level until we hit the cifs!
            for folder_name3 in os.listdir(
                os.path.join(base_directory, folder_name1, folder_name2)
            ):
                # we now have all the foldernames we need. Let's record the full path
                folder_path = os.path.join(
                    base_directory, folder_name1, folder_name2, folder_name3
                )

                # now go through each cif file in this directory
                for cif_filename in os.listdir(folder_path):

                    # construct the full path to the file we are after
                    cif_filepath = os.path.join(folder_path, cif_filename)

                    # Load the structure and extra data from the cif file.
                    # Note, some occupancies are not scaled to sum to 1. For
                    # example, a disordered site may have [Ca:1, Sr:1] instead of
                    # [Ca:0.5, Sr:0.5]. By setting our occupancy tolerance to
                    # infinity, we allow this  let pymatgen scale the occupancies
                    # so they sum to 1.
                    cif = CifParser(
                        cif_filepath,
                        occupancy_tolerance=float("inf"),
                    )
                    data = cif.as_dict()

                    # pull out the structure
                    # note we use CifParser.get_structures instead of
                    # Structure.from_file because we wanted the extra data too.
                    # The COD has a lot of structures that aren't formatted properly
                    # and various errors are thrown throughout the loading process.
                    # for now, I just skip the ones that give issues.
                    # !!! I should take a closer look at failed cifs in the future.
                    try:
                        structure = cif.get_structures()[0]
                    except ValueError as error:
                        if error.args != ("Invalid cif file with no structures!",):
                            raise error

                    # Run symmetry analysis and sanitization on the structure
                    structure_sanitized = get_sanitized_structure(structure)

                    if (
                        "Structure has implicit hydrogens defined, parsed structure"
                        " unlikely to be suitable for use in calculations unless"
                        " hydrogens added." in cif.warnings
                    ):
                        has_implicit_hydrogens = True
                    else:
                        has_implicit_hydrogens = False

                    # TESTING: for ordered structures, POSCAR won't work so I'm
                    # going to use CIF as the next best option until I make my
                    # new format.
                    if structure.is_ordered:
                        raise Exception

                    # Compile all of our data into a dictionary
                    # entry_dict = {
                    #     # the split removes ".cif" from each file name and
                    #     # the remaining number is the id
                    #     "id": cif_filename.split(".")[0],
                    #     "structure": structure_sanitized,
                    # }

                    # now convert the entry to a database object
                    # structure_db = CodStructure.from_pymatgen(**entry_dict)

                    # and save it to our database!
                    # structure_db.save()

                    # except:  # there are a bunch of different Exceptions...
                    #     # print(cif_filepath + " FAILED")
                    #     continue  # skip to the next structure


# --------------------------------------------------------------------------------------
