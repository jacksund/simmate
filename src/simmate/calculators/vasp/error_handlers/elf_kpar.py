# -*- coding: utf-8 -*-

import os

from simmate.workflow_engine import ErrorHandler
from simmate.calculators.vasp.inputs import Incar


class ElfKpar(ErrorHandler):

    is_monitor = True
    filename_to_check = "vasp.out"
    possible_error_messages = ["ELF: KPAR>1 not implemented"]

    def correct(self, directory: str) -> str:

        # load the INCAR file to view the current settings
        incar_filename = os.path.join(directory, "INCAR")
        incar = Incar.from_file(incar_filename)

        # make the fix
        incar["KPAR"] = 1
        correction = "switched KPAR to 1"

        # rewrite the INCAR with new settings
        incar.to_file(incar_filename)

        return correction
