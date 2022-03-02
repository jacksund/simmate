# -*- coding: utf-8 -*-

import os

from simmate.workflow_engine import ErrorHandler
from simmate.calculators.vasp.inputs import Incar


class TetrahedronMesh(ErrorHandler):
    """
    This handler addresses a series of error messages that are all caused by
    having incompatible tetrahedral mesh. In some cases, increasing the k-point
    mesh will fix the issue, and in other cases, we'll simply turn off the
    tetrahedron method.
    """

    is_monitor = True
    filename_to_check = "vasp.out"
    possible_error_messages = [
        "Tetrahedron method fails",
        "Fatal error detecting k-mesh",
        "Fatal error: unable to match k-point",
        "Routine TETIRR needs special values",
        "Tetrahedron method fails (number of k-points < 4)",
        "BZINTS",
        # This error is separate from the tetrahedral methods above, but it has
        # the same associated fix -- so we include it here.
        "DENTET",
    ]

    def correct(self, directory: str) -> str:

        # load the INCAR file to view the current settings
        incar_filename = os.path.join(directory, "INCAR")
        incar = Incar.from_file(incar_filename)

        # check what the current KSPACING is. If it's not set, that means we're using
        # the default which is 0.5.
        current_kspacing = incar.get("KSPACING", 0.5)

        # If KSPACING isn't the default value, we try decreasing KSPACING
        # by 20% in each direction. which approximately doubles the number
        # of kpoints.
        if current_kspacing != 0.5:
            new_kspacing = current_kspacing * 0.8
            incar["KSPACING"] = new_kspacing
            # rewrite the INCAR with new settings
            incar.to_file(incar_filename)
            return f"switched KSPACING from {current_kspacing} to {new_kspacing}"

        # otherwise we try changing the smearing method to guassian
        else:
            incar["ISMEAR"] = 0
            incar["SIGMA"] = 0.05
            # rewrite the INCAR with new settings
            incar.to_file(incar_filename)
            return "switched ISMEAR to 0 and SIGMA to 0.05"
