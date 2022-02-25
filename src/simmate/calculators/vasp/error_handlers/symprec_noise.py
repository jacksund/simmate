# -*- coding: utf-8 -*-

import os

from simmate.workflow_engine import ErrorHandler
from simmate.calculators.vasp.inputs import Incar


class SymprecNoise(ErrorHandler):
    """
    Fixes determination of symmetry in problematic structures.
    """

    is_monitor = True
    filename_to_check = "vasp.out"
    possible_error_messages = [
        "determination of the symmetry of your systems shows a strong"
    ]

    def correct(self, directory: str) -> str:

        # load the INCAR file to view the current settings
        incar_filename = os.path.join(directory, "INCAR")
        incar = Incar.from_file(incar_filename)

        # make the fix
        if incar.get("ISYM", 2) > 0 and incar.get("SYMPREC", 1e-5) > 1e-6:
            incar["SYMPREC"] = 1e-6
            correction = "switched SYMPREC to 1e-6"
        else:
            incar["ISYM"] = 0
            correction = "switched ISYM to 0"

        # rewrite the INCAR with new settings
        incar.to_file(incar_filename)

        return correction
