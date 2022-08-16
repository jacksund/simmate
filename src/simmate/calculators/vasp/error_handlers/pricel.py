# -*- coding: utf-8 -*-

from pathlib import Path

from simmate.calculators.vasp.inputs import Incar
from simmate.workflow_engine import ErrorHandler


class Pricel(ErrorHandler):
    """
    This fixes an internal VASP error by turning off symmetry.
    """

    is_monitor = True
    filename_to_check = "vasp.out"
    possible_error_messages = ["internal error in subroutine PRICEL"]

    def correct(self, directory: Path) -> str:

        # load the INCAR file to view the current settings
        incar_filename = directory / "INCAR"
        incar = Incar.from_file(incar_filename)

        # make the fix
        incar["SYMPREC"] = 1e-8
        incar["ISYM"] = 0
        correction = "switched ISYM to 0 and SYMPREC to 1e-8"

        # rewrite the INCAR with new settings
        incar.to_file(incar_filename)

        return correction
