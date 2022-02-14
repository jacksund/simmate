# -*- coding: utf-8 -*-

import os

from simmate.workflow_engine import ErrorHandler
from simmate.calculators.vasp.inputs import Incar


class IncorrectShift(ErrorHandler):
    """
    This handler addresses issues in the K-point mesh that can be fixed by switching
    to a gamma-centered mesh.
    """

    # run this while the VASP calculation is still going
    is_monitor = True

    # we assume that we are checking the vasp.out file
    filename_to_check = "vasp.out"

    # These are the error messages that we are looking for in the file
    possible_error_messages = [
        "Routine TETIRR needs special values",
        "Could not get correct shifts",
    ]

    def correct(self, directory):

        # load the INCAR file to view the current settings
        incar_filename = os.path.join(directory, "INCAR")
        incar = Incar.from_file(incar_filename)

        # Change to Gamma-centered mesh
        incar["KGAMMA"] = True

        # rewrite the INCAR with new settings
        incar.to_file(incar_filename)

        return "switched KGAMMA to True"
