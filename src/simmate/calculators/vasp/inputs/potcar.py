# -*- coding: utf-8 -*-

import os

# These are dictionaries that tell us which POTCARs we should grab based on
# the type of calculation as well as where to find them
from simmate.calculators.vasp.inputs.potcar_mappings import (
    FOLDER_MAPPINGS,
    PBE_ELEMENT_MAPPINGS,
    PBE_GW_ELEMENT_MAPPINGS,
    # TODO: LDA_ELEMENT_MAPPINGS
)


class Potcar:
    @staticmethod
    def to_file_from_type(
        elements,
        functional,
        filename="POTCAR",
        element_mappings=None,  # actual default is ELEMENT_MAPPINGS
    ):

        # Element objects are passed along with a string representing the
        # desired functional ("PBE", "LDA", or "PBE_GW")
        # The order of the elements list MUST match the POSCAR!

        # If the user wants to override the ELEMENT_MAPPINGS and use different
        # VASP potentials than what we have picked, then they can provide their
        # own dictionary OR pass in an update version of our. For example, they
        # may want to use the PBE potential of "C_h" instead of "C" which uses
        # a harder psuedopotential (useful in high-pressure and molecular
        # calculations). Here, they can do something like...
        #   element_mappings={"C": "C_h", ...} # with all of their other choices
        # or...
        #   element_mappings = PBE_ELEMENT_MAPPINGS.copy()
        #   element_mappings.update({"C": "C_h"})
        # NOTE: remember whereever you use update(), be careful and make sure
        # you update a copy of the imported dictionary and avoid logical bugs.
        # I don't do that here, but I know I'm not mutating the dictionary.
        # Otherwise, if nothing was supplied use our defaults:
        if not element_mappings:
            if functional == "PBE":
                element_mappings = PBE_ELEMENT_MAPPINGS
            if functional == "PBE_GW":
                element_mappings = PBE_GW_ELEMENT_MAPPINGS

        # based on the functional, grab the proper folder location of all POTCARs
        folder_loc = FOLDER_MAPPINGS[functional]

        # we mow need to iterate through each element and find it's POTCAR location
        # we also keep a list of where these are located
        potcar_locations = []
        for element in elements:

            # grab the proper POTCAR symbol based on the functional and element
            potcar_symbol = element_mappings[element.symbol]

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
