# -*- coding: utf-8 -*-

import os

from simmate.toolkit import Structure
from simmate.workflow_engine import ErrorHandler
from simmate.calculators.vasp.inputs import Incar
from simmate.calculators.vasp.outputs import Oszicar


class Zpotrf(ErrorHandler):
    """
    This handler attempts to fix a routine failure associated with LAPACK. The
    fix depends on the state of the calculation, so we check the OSZICAR to
    decide what to do.
    """

    is_monitor = True
    filename_to_check = "vasp.out"
    possible_error_messages = ["LAPACK: Routine ZPOTRF failed"]

    def correct(self, directory: str) -> str:

        # load the INCAR file to view the current settings
        incar_filename = os.path.join(directory, "INCAR")
        incar = Incar.from_file(incar_filename)

        # We can learn more about the cause of this error by looking at
        # the OSZICAR and checking the number of steps completed.
        # BUG: what if the OSCZICAR is improperly formatted but a number
        # of ionic steps completed successfully?
        try:
            oszicar_filename = os.path.join(directory, "OSZICAR")
            oszicar = Oszicar(oszicar_filename)
            nionic_steps = len(oszicar.ionic_steps)
        except Exception:
            nionic_steps = 0

        # If the error shows up after the first ionic step, then this is likely
        # caused by POTIM being too large.
        if nionic_steps >= 1:
            # Halve the POTIM and turn off symmetry
            current_potim = incar.get("POTIM", 0.5)
            new_potim = current_potim / 2
            incar["POTIM"] = new_potim
            incar["ISYM"] = 0
            correction = (
                f"set ISYM to 0 and switched POTIM from {current_potim} to {new_potim}"
            )

        # If this is a static calculation (NSW=0) or if ISIF is 1-3, then
        # we just want to turn off symmetry
        elif incar.get("NSW", 0) == 0 or incar.get("ISIF", 0) in [0, 1, 3]:
            incar["ISYM"] = 0
            correction = "set ISYM to 0"

        # If the error shows up on the first ionic step, it is likely that
        # our bond distances are too small. A simple fix is to scale our
        # starting lattice. We also save the original structure to a file
        # name POSCAR_original in case it's needed elsewhere.
        else:
            poscar_filename = os.path.join(directory, "POSCAR")
            structure = Structure.from_file(poscar_filename)
            structure.to("POSCAR", poscar_filename + "_original")
            structure.apply_strain(0.2)
            structure.to("POSCAR", poscar_filename)
            correction = "scaled the structure lattice by +20%"

        # Check the current ICHARG setting, where default is 0
        # If the ICHARG is less than 10, then we want to delete the CHGCAR
        # and WAVECAR to ensure the next run is a clean start.
        current_icharg = incar.get("ICHARG", 0)
        if current_icharg < 10:
            os.remove(os.path.join(directory, "CHGCAR"))
            os.remove(os.path.join(directory, "WAVECAR"))
            correction += " and deleted CHGCAR and WAVECAR"

        # rewrite the INCAR with new settings
        incar.to_file(incar_filename)

        # now return the correction made for logging
        return correction
