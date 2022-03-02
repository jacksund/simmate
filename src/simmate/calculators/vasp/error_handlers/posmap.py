# -*- coding: utf-8 -*-

import os
import json

from simmate.workflow_engine import ErrorHandler
from simmate.calculators.vasp.inputs import Incar


class Posmap(ErrorHandler):

    is_monitor = True
    filename_to_check = "vasp.out"
    possible_error_messages = ["POSMAP"]

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
        # If it isn't there yet, set the count to 0 and we'll update it below.
        error_counts["posmap"] = error_counts.get("posmap", 0) + 1

        # VASP advises to decrease or increase SYMPREC by an order of magnitude
        # the default SYMPREC value is 1e-5
        if error_counts["posmap"] == 0:
            # first, reduce by 10x
            current_symprec = incar.get("SYMPREC", 1e-5)
            new_symprec = current_symprec / 10
            incar["SYMPREC"] = new_symprec
            correction = f"switched SYMPREC from {current_symprec} to {new_symprec}"

        elif error_counts["posmap"] == 1:
            # next, increase by 100x (10x the original because we descreased
            # by 10x in the first try.)
            current_symprec = incar.get("SYMPREC", 1e-5)
            new_symprec = current_symprec * 100
            incar["SYMPREC"] = new_symprec
            correction = f"switched SYMPREC from {current_symprec} to {new_symprec}"

        # increase our attempt count
        error_counts["posmap"] += 1

        # rewrite the new error count file
        with open(error_count_filename, "w") as file:
            json.dump(error_counts, file)

        # rewrite the INCAR with new settings
        incar.to_file(incar_filename)

        return correction
