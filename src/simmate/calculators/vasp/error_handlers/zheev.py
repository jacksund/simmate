# -*- coding: utf-8 -*-

import os

from simmate.workflow_engine import ErrorHandler
from simmate.calculators.vasp.inputs import Incar


class Zheev(ErrorHandler):

    is_monitor = True
    filename_to_check = "vasp.out"
    possible_error_messages = ["ERROR EDDIAG: Call to routine ZHEEV failed!"]

    def correct(self, directory: str) -> str:

        # load the INCAR file to view the current settings
        incar_filename = os.path.join(directory, "INCAR")
        incar = Incar.from_file(incar_filename)

        # We make a fix only if ALGO is set less to Fast
        if incar.get("ALGO", "Fast") != "Exact":
            incar["ALGO"] = "Exact"
            correction = "switched Algo to Exact"

        # rewrite the INCAR with new settings
        incar.to_file(incar_filename)

        return correction
