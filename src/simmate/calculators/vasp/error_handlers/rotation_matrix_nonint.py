# -*- coding: utf-8 -*-

import os

from simmate.workflow_engine.error_handler import ErrorHandler
from simmate.calculators.vasp.inputs.incar import Incar


class RotationMatrix(ErrorHandler):
    """
    This a simple error handler that is active when VASP finds an issue with the
    rotation matrix.
    """

    # run this while the VASP calculation is still going
    is_monitor = True

    # we assume that we are checking the vasp.out file
    filename_to_check = "vasp.out"

    # These are the error messages that we are looking for in the file
    possible_error_messages = [
        "Found some non-integer element in rotation matrix",
        "SGRCON",
    ]

    def correct(self, directory):

        # load the INCAR file to view the current settings
        incar_filename = os.path.join(directory, "INCAR")
        incar = Incar.from_file(incar_filename)

        # switch to gamma-centered mesh
        incar["KGAMMA"] = True
        correction = "switched KGAMMA to True"
        # TODO: 2nd attempt is to turn ISYM=0

        # rewrite the INCAR with new settings
        incar.to_file(incar_filename)

        return correction
