# -*- coding: utf-8 -*-

import os

from simmate.workflow_engine import ErrorHandler
from simmate.calculators.vasp.inputs import Incar


class Eddrmm(ErrorHandler):
    """
    This is an error caused by failed call to LAPCK.

    This could be caused by a number of things, such as instability of the
    RMM-DIIS diagonalisation algorithm, an unreasonable crystal geometry, or
    even just incorrect installation of LAPCK.

    Further discussion is also located on VASP's forum
    [here](https://www.vasp.at/forum/viewtopic.php?f=3&t=214&p=215).
    """

    is_monitor = True
    filename_to_check = "vasp.out"
    possible_error_messages = ["WARNING in EDDRMM: call to ZHEGV failed"]

    def correct(self, directory: str) -> str:

        # load the INCAR file to view the current settings
        incar_filename = os.path.join(directory, "INCAR")
        incar = Incar.from_file(incar_filename)

        # RMM algorithm is not stable for this calculation
        if incar.get("ALGO", "Normal") in ["Fast", "VeryFast"]:
            incar["ALGO"] = "Normal"
            correction = "switched ALGO to Normal"
        else:
            # Halve the POTIM
            current_potim = incar.get("POTIM", 0.5)
            new_potim = current_potim / 2
            incar["POTIM"] = new_potim
            correction = f"switch POTIM from {current_potim} to {new_potim}"

        # Check the current ICHARG setting, where default is 0
        # If the ICHARG is less than 10, then we want to delete the CHGCAR
        # and WAVECAR to ensure the next run is a clean start.
        current_icharg = incar.get("ICHARG", 0)
        if current_icharg < 10:

            # check if IMAGES is in the INCAR. If so, we have a NEB calculation,
            # and the there will be a different organization of folders.
            if "IMAGES" in incar.keys():
                # here, folders will be 00, 01, 02, etc. with CHGCARs/WAVECARs
                # in each. We iterate through and delete all of them.
                subdirectories = [d for d in os.listdir(directory) if d.isnumeric()]
                for subdir in subdirectories:
                    chgcar_filename = os.path.join(directory, subdir, "CHGCAR")
                    wavecar_filename = os.path.join(directory, subdir, "WAVECAR")
                    if os.path.exists(chgcar_filename):
                        os.remove(chgcar_filename)
                    if os.path.exists(wavecar_filename):
                        os.remove(wavecar_filename)
                correction += " and deleted CHGCARs + WAVECARs for all images"

            # Otherwise, we have a normal VASP calculation
            else:
                os.remove(os.path.join(directory, "CHGCAR"))
                os.remove(os.path.join(directory, "WAVECAR"))
                correction += " and deleted CHGCAR + WAVECAR"
        # rewrite the INCAR with new settings
        incar.to_file(incar_filename)

        return correction
