# -*- coding: utf-8 -*-

from pathlib import Path

from simmate.calculators.vasp.inputs import Incar
from simmate.workflow_engine import ErrorHandler


class IncorrectShift(ErrorHandler):
    """
    This handler addresses issues in the K-point mesh that can be fixed by switching
    to a gamma-centered mesh.
    """

    is_monitor = True
    filename_to_check = "vasp.out"
    possible_error_messages = ["Could not get correct shifts"]

    def correct(self, directory: Path) -> str:

        # load the INCAR file to view the current settings
        incar_filename = directory / "INCAR"
        incar = Incar.from_file(incar_filename)

        # Change to Gamma-centered mesh
        incar["KGAMMA"] = True

        # rewrite the INCAR with new settings
        incar.to_file(incar_filename)

        return "switched KGAMMA to True"
