# -*- coding: utf-8 -*-

import os

from simmate.workflow_engine import ErrorHandler
from simmate.calculators.vasp.inputs import Incar


class Edddav(ErrorHandler):
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

        correction = ""
        # Delete the CHGCAR if this is a "from-scratch" calc
        current_icharg = incar.get("ICHARG", 0)
        if current_icharg < 10:
            os.remove(os.path.join(dir, "CHGCAR"))
            correction += "deleted CHGCAR and "
        incar["ALGO"] = "All"
        correction += "switched ALGO to Normal"

        # rewrite the INCAR with new settings
        incar.to_file(incar_filename)

        return correction
