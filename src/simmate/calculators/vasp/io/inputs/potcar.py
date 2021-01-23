# -*- coding: utf-8 -*-

import os

# These are dictionaries that tell us which POTCARs we should grab based on
# the type of calculation as well as where to find them
from simmate.calculators.vasp.io.inputs.potcar_mappings import (
    ELEMENT_MAPPINGS,
    FOLDER_MAPPINGS,
)


class Potcar:
    @staticmethod
    def write_from_type(elements, functional, filename="POTCAR"):

        # an Element objects are passed along with a string representing the
        # desired functional ("PBE", "LDA", or "PBE_GW")
        # !!! The order of the elements list MUST match the POSCAR!

        # based on the functional, grab the proper folder location of all POTCARs
        folder_loc = FOLDER_MAPPINGS[functional]

        # we mow need to iterate through each element and find it's POTCAR location
        # we also keep a list of where these are located
        potcar_locations = []
        for element in elements:

            # grab the proper POTCAR symbol based on the functional and element
            potcar_symbol = ELEMENT_MAPPINGS[functional][element.symbol]

            # now let's combine this information for the full path to the POTCAR.
            # The file will be located at /folder_loc/element_symbol/POTCAR
            potcar_loc = os.path.join(folder_loc, potcar_symbol, "POTCAR")

            # add it to our list
            potcar_locations.append(potcar_loc)

        # VASP expect all POTCAR files to be combined into one and in the same
        # order as the POSCAR elements. Let's do that here.
        with open(filename, "w") as combinedfile:
            for potcar in potcar_locations:
                with open(potcar) as singlefile:
                    combinedfile.write(singlefile.read())

    # TODO
    # from_symbol_and_functional --> returns Potential object
    # from_file --> returns Potential object
    # write_from_potential --> takes a Potential object and write file in POTCAR format
    # symbols --> gives list of potcar symbols (Ca, Y_sv, etc.)
    # nelect --> gives total electron count from potcar
