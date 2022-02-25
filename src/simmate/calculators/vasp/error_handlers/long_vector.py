# -*- coding: utf-8 -*-

import os

from simmate.workflow_engine import ErrorHandler
from simmate.calculators.vasp.inputs import Incar


class LongVector(ErrorHandler):
    """
    This a simple error handler that is active when VASP finds an issue with the
    rotation matrix.
    """

    is_monitor = True
    filename_to_check = "vasp.out"
    possible_error_messages = [
        "One of the lattice vectors is very long (>50 A), but AMIN"
    ]

    def correct(self, directory: str) -> str:

        # load the INCAR file to view the current settings
        incar_filename = os.path.join(directory, "INCAR")
        incar = Incar.from_file(incar_filename)

        # make the fix
        incar["AMIN"] = 0.01
        correction = "switched AMIN to 0.01"

        # rewrite the INCAR with new settings
        incar.to_file(incar_filename)

        return correction
