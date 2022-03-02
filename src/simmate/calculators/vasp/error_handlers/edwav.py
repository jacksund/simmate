# -*- coding: utf-8 -*-

import os

from simmate.workflow_engine import ErrorHandler
from simmate.calculators.vasp.inputs import Incar


class Edwav(ErrorHandler):
    """
    When the gradient is not orthogonal, we make a fix depending on what IMSEAR
    is set to.
    """

    is_monitor = True
    filename_to_check = "vasp.out"
    possible_error_messages = ["EDWAV: internal error, the gradient is not orthogonal"]

    def correct(self, directory: str) -> str:

        # load the INCAR file to view the current settings
        incar_filename = os.path.join(directory, "INCAR")
        incar = Incar.from_file(incar_filename)

        # We make a fix only if IMSEAR is set less than 0
        if incar.get("ISMEAR", 1) < 0:
            incar["ISMEAR"] = "0"
            incar["SIGMA"] = 0.05
            correction = "switched SIGMA to 0.05 and ALGO to Normal"

        # rewrite the INCAR with new settings
        incar.to_file(incar_filename)

        return correction
