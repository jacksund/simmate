# -*- coding: utf-8 -*-

import os
import json

from simmate.workflow_engine import ErrorHandler
from simmate.calculators.vasp.inputs import Incar


class SubspaceMatrix(ErrorHandler):
    """
    This handler fixes when the sub-space-matrix is not hermitian. On the first
    attempt, we switch evaluation of projection operators to reciprocal space.
    If that doesn't work, the calculation precision is switched to "Accurate".
    """

    is_monitor = True
    filename_to_check = "vasp.out"
    possible_error_messages = ["WARNING: Sub-Space-Matrix is not hermitian in DAV"]

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
        # fix this. So let's make sure it's in our error_count dictionary.
        # If it isn't there yet, set the count to 0.
        # Also increase the count by 1, as this is our new addition
        error_counts["subspacematrix"] = error_counts.get("subspacematrix", 0) + 1

        # On our first try, change evalutating projection operators
        # in reciprocal space.
        if error_counts["subspacematrix"] == 0:
            incar["LREAL"] = False
            correction = "set LREAL to False"
        # As a last resort, try changing the precision
        else:
            incar["PREC"] = "Accurate"
            correction = "set PREC to Accurate"

        # rewrite the INCAR with new settings
        incar.to_file(incar_filename)

        # rewrite the new error count file
        with open(error_count_filename, "w") as file:
            json.dump(error_counts, file)

        # now return the correction made for logging
        return correction
