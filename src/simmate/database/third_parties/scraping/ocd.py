# -*- coding: utf-8 -*-


"""

This file is for pulling OCD data into the Simmate database. 

The OCD let's you download all of their data as a zip file. While they do have a
REST API, it looks like they prefer you to use the zip file if you want all structures
and metadata. This is a big download even when compressed (17GB), so it's a slow
process -- but more importantly a stable one. For future reference though, the REST
API is outlined here: https://wiki.crystallography.net/RESTful_API/

Once downloaded, all of the cif files are organized into folders based on their first
few numbers -- for example, the cif 1234567 would be in folder /cif/1/23/45/1234567.cif
It's an odd way of storing the files, but we just need to script opening all of the folders
open. Note that some folders also don't have any cifs in them! There is also extra data
in each cif file -- such as the doi of the paper it came from.

There looks to be a lot of problematic cif files in the OCD, but it's not worth parsing
through all of these. Instead, I simply try to load the cif file into a pymatgen
Structure object, and if it fails, I just move on.

"""

import os

from django.db import transaction

from tqdm import tqdm
from pymatgen.core.structure import Structure

from simmate.configuration.django import setup_full  # sets up database

from simmate.database.third_parties.ocd import OcdStructure
from simmate.database.third_parties.scraping.utilities import get_sanitized_structure

# --------------------------------------------------------------------------------------


@transaction.atomic
def load_all_structures(base_directory="ocd/cif/"):

    # We need to look at all the folders that have numbered names (1,2,3..,9). and
    # grab the folder inside that are also numbers. This continues until we find cif
    # files that we can pull structures from. Note the name of the cif file is also
    # the ocd-id.
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
                    
                    # The OCD has a lot of structures that aren't formatted properly
                    # and various errors are thrown throughout the loading process.
                    # for now, I just skip the ones that give issues.
                    # !!! I should take a closer look at failed cifs in the future.
                    try:
                        # load the structure from the cif file
                        structure = Structure.from_file(cif_filepath)
                        
                        # Run symmetry analysis and sanitization on the structure
                        structure_sanitized = get_sanitized_structure(structure)

                        # TODO: For now I just record the structure and ocd-id, but I 
                        # should pull metadata in the future. To do this, I can use 
                        # pymatgen.io.cif.CifFile to parse the data.
                        # Here's how you would grab the data...
                        #   from pymatgen.io.cif import CifFile
                        #   file = CifFile.from_file(filename_cif)
                        #   # grab the first data entry. There also should only be one
                        #   # but it is possible
                        #   # for a cif file to have more than one structure.
                        #   entry = file.data[0]
                        #   entry_data = entry.data
    
                        # Compile all of our data into a dictionary
                        entry_dict = {
                            # the split removes ".cif" from each file name and 
                            # the remaining number is the id
                            "id": cif_filename.split(".")[0],
                            "structure": structure_sanitized,
                        }
    
                        # now convert the entry to a database object
                        structure_db = OcdStructure.from_pymatgen(**entry_dict)
    
                        # and save it to our database!
                        structure_db.save()

                    except:  # there are a bunch of different Exceptions...
                        # print(cif_filepath + " FAILED")
                        continue  # skip to the next structure

# --------------------------------------------------------------------------------------
