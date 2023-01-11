# -*- coding: utf-8 -*-

from pathlib import Path

from simmate.calculators.vasp.error_handlers import IncorrectShift, TetrahedronMesh
from simmate.workflow_engine import ErrorHandler


class Tetirr(ErrorHandler):
    """
    This handler addresses an issue that is a combination of the TetrahedronMesh
    and IncorrectShift errors.
    """

    is_monitor = True
    filename_to_check = "vasp.out"
    possible_error_messages = ["Routine TETIRR needs special values"]

    def correct(self, directory: Path) -> str:

        # apply the fixes uses these other error handlers
        fixes_1 = TetrahedronMesh().correct(directory)
        fixes_2 = IncorrectShift().correct(directory)

        # combine the output messages and return
        return f"{fixes_1} and {fixes_2}"
