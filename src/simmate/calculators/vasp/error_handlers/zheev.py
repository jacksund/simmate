# -*- coding: utf-8 -*-

from pathlib import Path

from simmate.calculators.vasp.inputs import Incar
from simmate.workflow_engine import ErrorHandler


class Zheev(ErrorHandler):

    is_monitor = True
    filename_to_check = "vasp.out"
    possible_error_messages = ["ERROR EDDIAG: Call to routine ZHEEV failed!"]

    def correct(self, directory: Path) -> str:

        # load the INCAR file to view the current settings
        incar_filename = directory / "INCAR"
        incar = Incar.from_file(incar_filename)

        # We make a fix only if ALGO is set less to Fast
        if incar.get("ALGO", "Fast") != "Exact":
            incar["ALGO"] = "Exact"
            correction = "switched Algo to Exact"

        # rewrite the INCAR with new settings
        incar.to_file(incar_filename)

        return correction
