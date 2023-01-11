# -*- coding: utf-8 -*-

from pathlib import Path

from simmate.calculators.vasp.inputs import Incar
from simmate.workflow_engine import ErrorHandler


class Rhosyg(ErrorHandler):

    is_monitor = True
    filename_to_check = "vasp.out"
    possible_error_messages = ["RHOSYG"]

    def correct(self, directory: Path) -> str:

        # load the INCAR file to view the current settings
        incar_filename = directory / "INCAR"
        incar = Incar.from_file(incar_filename)

        # We make a fix only if SYMPREC is not the default value
        if incar.get("SYMPREC", 1e-4) == 1e-4:
            incar["ISYM"] = 0
            correction = "switched ISYM to 0"
        else:
            correction = ""

        incar["SYMPREC"] = 1e-4
        correction += "switched SYMPREC back to default (1e-4)"

        # rewrite the INCAR with new settings
        incar.to_file(incar_filename)

        return correction
