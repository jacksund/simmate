# -*- coding: utf-8 -*-

import os

from simmate.workflow_engine import ErrorHandler
from simmate.calculators.vasp.inputs import Incar


class InsufficientBands(ErrorHandler):
    """
    If the calculation has too few bands, we increase the number of bands by
    10% and try again.
    """

    is_monitor = True
    filename_to_check = "vasp.out"
    possible_error_messages = ["TOO FEW BANDS"]

    def correct(self, directory: str) -> str:

        # load the INCAR file to view the current settings
        incar_filename = os.path.join(directory, "INCAR")
        incar = Incar.from_file(incar_filename)

        # Grab the current number of bands. First check the INCAR and if
        # it isn't there, jump to the OUTCAR.
        if "NBANDS" in incar:
            nbands_current = incar["NBANDS"]
        else:
            outcar_filename = os.path.join(directory, "OUTCAR")
            with open(outcar_filename) as file:
                lines = file.readlines()
            # Go through the lines until we find the NBANDS. The value
            # should be at the very end of the line.
            for line in lines:
                if "NBANDS" in line:
                    nbands_current = int(line.split()[-1])
                    break
        # increase the number of bands by 10%
        nbands_new = int(nbands_current * 1.1)
        incar["NBANDS"] = nbands_new
        correction = f"switch NBANDS from {nbands_current} to {nbands_new} (+10%)"

        # rewrite the INCAR with new settings
        incar.to_file(incar_filename)

        return correction
