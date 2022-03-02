# -*- coding: utf-8 -*-

import os

from simmate.workflow_engine import ErrorHandler
from simmate.calculators.vasp.inputs import Incar


class Brions(ErrorHandler):
    """
    This fixes an internal VASP error by increasing POTIM.
    """

    is_monitor = True
    filename_to_check = "vasp.out"
    possible_error_messages = ["BRIONS problems: POTIM should be increased"]

    def correct(self, directory: str) -> str:

        # load the INCAR file to view the current settings
        incar_filename = os.path.join(directory, "INCAR")
        incar = Incar.from_file(incar_filename)

        # make the fix
        current_potim = incar.get("POTIM", 0.5)
        new_potim = current_potim + 0.1
        incar["POTIM"] = new_potim
        correction = f"switched POTIM from {current_potim} to {new_potim}"

        # rewrite the INCAR with new settings
        incar.to_file(incar_filename)

        return correction
