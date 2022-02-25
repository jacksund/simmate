# -*- coding: utf-8 -*-

import os

from simmate.workflow_engine import ErrorHandler
from simmate.calculators.vasp.inputs import Incar


class RotationMatrix(ErrorHandler):
    """
    This a simple error handler that is active when VASP struggles to find the
    rotation matrix. VASP gives us the suggested fix directly, which is to
    simply increase the symmetry precision.
    """

    is_monitor = True
    filename_to_check = "vasp.out"
    possible_error_messages = ["rotation matrix was not found (increase SYMPREC)"]

    def correct(self, directory: str) -> str:

        # load the INCAR file to view the current settings
        incar_filename = os.path.join(directory, "INCAR")
        incar = Incar.from_file(incar_filename)

        # increase the precision
        incar["SYMPREC"] = 1e-8

        # rewrite the INCAR with new settings
        incar.to_file(incar_filename)

        return "switched SYMPREC to 1e-8"
