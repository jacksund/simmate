# -*- coding: utf-8 -*-

import os
import shutil

from simmate.workflow_engine import ErrorHandler
from simmate.calculators.vasp.inputs import Incar


class Zbrent(ErrorHandler):
    """
    Calculation is simply restarted using the most recent structure (CONTCAR)
    """

    is_monitor = True
    filename_to_check = "vasp.out"
    possible_error_messages = [
        "ZBRENT: fatal internal in",
        "ZBRENT: fatal error in bracketing",
    ]

    def correct(self, directory: str) -> str:

        # load the INCAR file to view the current settings
        incar_filename = os.path.join(directory, "INCAR")
        incar = Incar.from_file(incar_filename)

        # make the fix
        incar["IBRION"] = 1
        poscar_filename = os.path.join(directory, "POSCAR")
        contcar_filename = os.path.join(directory, "CONTCAR")
        shutil.copyfile(contcar_filename, poscar_filename)
        correction = "switched IBRION to 1 and copied the CONTCAR over to the POSCAR"

        # rewrite the INCAR with new settings
        incar.to_file(incar_filename)

        return correction
