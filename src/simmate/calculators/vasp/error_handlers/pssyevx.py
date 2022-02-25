# -*- coding: utf-8 -*-

import os

from simmate.workflow_engine import ErrorHandler
from simmate.calculators.vasp.inputs import Incar


class Pssyevx(ErrorHandler):
    """
    This fixes subspace rotation error by switching ALGO to Normal
    """

    is_monitor = True
    filename_to_check = "vasp.out"
    possible_error_messages = ["ERROR in subspace rotation PSSYEVX"]

    def correct(self, directory: str) -> str:

        # load the INCAR file to view the current settings
        incar_filename = os.path.join(directory, "INCAR")
        incar = Incar.from_file(incar_filename)

        # make the fix
        incar["ALGO"] = "Normal"
        correction = "switched ALGO to Normal"

        # rewrite the INCAR with new settings
        incar.to_file(incar_filename)

        return correction
