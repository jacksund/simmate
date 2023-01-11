# -*- coding: utf-8 -*-

from pathlib import Path

from simmate.calculators.vasp.inputs import Incar
from simmate.workflow_engine import ErrorHandler


class Pssyevx(ErrorHandler):
    """
    This fixes subspace rotation error by switching ALGO to Normal
    """

    is_monitor = True
    filename_to_check = "vasp.out"
    possible_error_messages = ["ERROR in subspace rotation PSSYEVX"]

    def correct(self, directory: Path) -> str:

        # load the INCAR file to view the current settings
        incar_filename = directory / "INCAR"
        incar = Incar.from_file(incar_filename)

        # make the fix
        incar["ALGO"] = "Normal"
        correction = "switched ALGO to Normal"

        # rewrite the INCAR with new settings
        incar.to_file(incar_filename)

        return correction
