# -*- coding: utf-8 -*-

import os

from simmate.workflow_engine.error_handler import ErrorHandler
from simmate.calculators.vasp.inputs.incar import Incar


class Rhosyg(ErrorHandler):
    """
    ???
    """

    # run this while the VASP calculation is still going
    is_monitor = True

    # we assume that we are checking the vasp.out file
    filename_to_check = "vasp.out"

    # These are the error messages that we are looking for in the file
    possible_error_messages = ["RHOSYG"]

    def correct(self, directory):

        # load the INCAR file to view the current settings
        incar_filename = os.path.join(directory, "INCAR")
        incar = Incar.from_file(incar_filename)

        # We make a fix only if SYMPREC is not the default value
        if incar.get("SYMPREC", 1e-4) == 1e-4:
            incar["ISYM"] = 0
            correction = "switched ISYM to 0"
        else:
            correction = ""

        incar["SYMPREC"] = 1e-4
        correction += "switched SYMPREC back to default (1e-4)"

        # rewrite the INCAR with new settings
        incar.to_file(incar_filename)

        return correction
