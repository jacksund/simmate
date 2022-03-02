# -*- coding: utf-8 -*-

import os
import shutil

from pymatgen.io.vasp.outputs import Vasprun

from simmate.workflow_engine import ErrorHandler
from simmate.calculators.vasp.inputs import Incar


class Unconverged(ErrorHandler):
    """
    Check if a calculation converged successfully. If not, the fix depends on
    whether its the ionic steps or electronic steps are struggling to converge.

    NOTE: This can be confusing when used along with the Nonconverging error handler
    because both attempt to fix failures in electronic convergence. These handlers
    are converted directly from Custodian, so it's not clear to me why they
    separated them. In the future, I need to clean this up.
    """

    is_monitor = False

    def check(self, directory: str) -> bool:

        # Now check if the calculation converged. If not, we have the error!
        xml_filename = os.path.join(directory, "vasprun.xml")
        try:
            # load the xml file and only parse the bare minimum
            xmlReader = Vasprun(
                filename=xml_filename,
                parse_dos=False,
                parse_eigen=False,
                parse_projected_eigen=False,
                parse_potcar_file=False,
                exception_on_bad_xml=True,
            )
            if not xmlReader.converged:
                return True
        except Exception:
            pass

        # if the xml fails to load or if it converged successfully, then we
        # don't have this error.
        return False

    def correct(self, directory: str) -> str:

        # load the INCAR file to view the current settings
        incar_filename = os.path.join(directory, "INCAR")
        incar = Incar.from_file(incar_filename)

        # Also load the vasp results to see if it's the electronic or ionic steps
        # that are failing to converge.
        xml_filename = os.path.join(directory, "vasprun.xml")
        xmlReader = Vasprun(
            filename=xml_filename,
            parse_dos=False,
            parse_eigen=False,
            parse_projected_eigen=False,
            parse_potcar_file=False,
            exception_on_bad_xml=True,
        )

        # check if the electronic steps converged
        if not xmlReader.converged_electronic:
            # Here we switch the ALGO from VeryFast --> Fast --> Normal as
            # each ALGO is increasingly more stable but computationally more
            # expensive.

            # grab what was previously used as the ALGO, where the default is Normal
            current_algo = incar.get("ALGO", "Normal")

            # If the current algo is VeryFast, then switch it to Fast
            if current_algo == "VeryFast":
                # Set the new value
                incar["ALGO"] = "Fast"
                # rewrite the new INCAR file
                incar.to_file(incar_filename)
                # return the description of what we did
                return "switched ALGO from VeryFast to Fast"

            # If the current algo is Fast, then switch it to Normal
            elif current_algo == "Fast":
                # Set the new value
                incar["ALGO"] = "Normal"
                # rewrite the new INCAR file
                incar.to_file(incar_filename)
                # return the description of what we did
                return "switched ALGO from Fast to Normal"

            # If the current algo is Normal, then switch it to All
            elif current_algo == "Normal":
                # Set the new value
                incar["ALGO"] = "All"
                # rewrite the new INCAR file
                incar.to_file(incar_filename)
                # return the description of what we did
                return "switched ALGO from Normal to All"

            # As a last resort we try to introduce mixing
            else:
                new_settings = {
                    "ISTART": 1,
                    "ALGO": "Normal",
                    "NELMDL": -6,
                    "BMIX": 0.001,
                    "AMIX_MAG": 0.8,
                    "BMIX_MAG": 0.001,
                }
                # check that we dont already have these values set first
                if not all(
                    incar.get(key) == value for key, value in new_settings.items()
                ):
                    # Set the new values
                    incar.update(new_settings)
                    # rewrite the new INCAR file
                    incar.to_file(incar_filename)
                    # return the description of what we did
                    return (
                        f"turned on mixing with the following settings: {new_settings}"
                    )

        # if it's not electronic convergence, check it is the ionic steps
        elif not xmlReader.converged_ionic:
            # We continue the optimization with RMM-DIIS type relaxation

            # Copy the CONTCAR into the POSCAR
            poscar_filename = os.path.join(directory, "POSCAR")
            contcar_filename = os.path.join(directory, "CONTCAR")
            shutil.copy(contcar_filename, poscar_filename)
            correction = "copied the CONTCAR into the POSCAR"

            # update the INCAR if it isn't already IBRION=1
            current_ibrion = incar.get("IBRION", 0)
            if current_ibrion != 1:
                incar["IBRION"] = 1
                incar.to_file(incar_filename)
                correction += " and switched IBRION to 1"

            return correction
