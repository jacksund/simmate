# -*- coding: utf-8 -*-

import os
import json

from simmate.workflow_engine import ErrorHandler
from simmate.calculators.vasp.inputs import Incar


class RotationNonIntMatrix(ErrorHandler):
    """
    This a simple error handler that is active when VASP finds an issue with the
    rotation matrix.
    """

    is_monitor = True
    filename_to_check = "vasp.out"
    possible_error_messages = [
        "Found some non-integer element in rotation matrix",
        "SGRCON",
    ]

    def correct(self, directory: str) -> str:

        # load the INCAR file to view the current settings
        incar_filename = os.path.join(directory, "INCAR")
        incar = Incar.from_file(incar_filename)

        # load the error-count file if it exists
        error_count_filename = os.path.join(directory, "simmate_error_counts.json")
        if os.path.exists(error_count_filename):
            with open(error_count_filename) as error_count_file:
                error_counts = json.load(error_count_file)
        # otherwise we are starting with an empty dictionary
        else:
            error_counts = {}

        # The fix is based on the number of times we've already tried to
        # fix brmix. So let's make sure it's in our error_count dictionary.
        # If it isn't there yet, set the count to 0 and we'll update it below.
        error_counts["brmix"] = error_counts.get("brmix", 0)

        # Our first attempt to fix this error is to switch to a gamma-centered mesh
        if error_counts["brmix"] == 0:
            # switch to gamma-centered mesh
            incar["KGAMMA"] = True
            correction = "switched KGAMMA to True"

        # our second attempt turns symmetry off
        elif error_counts["brmix"] == 1:

            incar["ISYM"] = 0
            correction = "switched KGAMMA to True"

        # if the two attempts above didn't work, we give up by raising an error
        else:
            raise Exception(
                "Exceeded maximum corrections for RotationNonIntMatrix error."
            )

        # rewrite the INCAR with new settings
        incar.to_file(incar_filename)

        # rewrite the new error count file
        with open(error_count_filename, "w") as file:
            json.dump(error_counts, file)

        # now return the correction made for logging
        return correction
