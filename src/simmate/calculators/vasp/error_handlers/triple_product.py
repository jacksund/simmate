# -*- coding: utf-8 -*-

import os

from simmate.toolkit import Structure
from simmate.workflow_engine import ErrorHandler
from simmate.calculators.vasp.inputs import Incar


class TripleProduct(ErrorHandler):
    """
    This error handler swaps the b and c lattice vectors when VASP fails to handle
    its basis vectors properly.
    """

    is_monitor = True
    filename_to_check = "vasp.out"
    possible_error_messages = ["ERROR: the triple product of the basis vectors"]

    def correct(self, directory: str) -> str:

        # load the INCAR file to view the current settings
        incar_filename = os.path.join(directory, "INCAR")
        incar = Incar.from_file(incar_filename)

        # load the structure and save it as a backup file
        poscar_filename = os.path.join(directory, "POSCAR")
        structure = Structure.from_file(poscar_filename)
        structure.to("POSCAR", poscar_filename + "_original")

        # switch the b and c lattice vector of the structure
        structure.make_supercell([[1, 0, 0], [0, 0, 1], [0, 1, 0]])
        structure.to("POSCAR", poscar_filename)
        correction = "adjusted lattice basis to swap b and c vectors"

        # rewrite the INCAR with new settings
        incar.to_file(incar_filename)

        return correction
