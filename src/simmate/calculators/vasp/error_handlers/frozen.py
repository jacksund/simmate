# -*- coding: utf-8 -*-

import os
import time

from simmate.workflow_engine import ErrorHandler
from simmate.calculators.vasp.inputs import Incar


class Frozen(ErrorHandler):
    """
    Checks when the output file has last been editted. If the job has been sitting
    for a long time (i.e. 1 hour), we consider it frozen and want to change the
    ALGO from Normal to Fast or alternatively reduce SYMPREC.
    """

    is_monitor = True

    def __init__(self, timeout_limit: float = 3600):
        self.timeout_limit = timeout_limit

    def check(self, directory: str) -> bool:
        """
        Check for error in the specified directory. Note, we assume that we are
        checking the vasp.out file. If that file is not present, we say that there
        is no error because another handler will address this.
        """

        # establish the full path to the output file
        output_filename = os.path.join(directory, "vasp.out")

        # check to see that the file is there first
        if os.path.exists(output_filename):

            # check when the file was last editted
            time_last_edit = os.path.getmtime(output_filename)

            # see how long ago this was and if it was longer than our timeout
            if time.time() - time_last_edit > self.timeout_limit:

                # if so, we have a frozen error and need to report it
                return True

        # If the file doesn't exist, we are not seeing any error yet.
        # This line will also be reached if the last edit of the file was under
        # our timeout specified -- where the job is still running and looks good.
        return False

    def correct(self, directory: str) -> str:

        # load the INCAR file to view the current settings
        incar_filename = os.path.join(directory, "INCAR")
        incar = Incar.from_file(incar_filename)

        #########
        # UNIQUE TO SIMMATE (i.e. changed from original custodian FrozenHandler)
        # if Kerker mixing is present (IMIX=1), then this error was likely caused
        # by the Brmix handler. We therefore delete this setting and retry.
        # See https://github.com/jacksund/simmate/issues/159
        if incar.get("IMIX", None) == 1:
            # delete the CHGCAR and WAVECAR to ensure the next run is a clean start.
            os.remove(os.path.join(directory, "CHGCAR"))
            os.remove(os.path.join(directory, "WAVECAR"))
            incar.pop("IMIX")
            incar.to_file(incar_filename)
            return "Removed IMIX=1 and deleted CHGCAR and WAVECAR"
        #########

        # check what the current ALGO is. If it's not set, that means it's using
        # the default which is "Normal".
        current_algo = incar.get("ALGO", "Normal")
        # also check the SYMPREC, where default is 1e-5
        current_symprec = incar.get("SYMPREC", "1e-5")

        # If the current algo is Fast, then switch it to Normal
        if current_algo == "Fast":
            # Set the new value
            incar["ALGO"] = "Normal"
            # rewrite the new INCAR file
            incar.to_file(incar_filename)
            # return the description of what we did
            return "switched ALGO from Fast to Normal"

        # If the ALGO didn't do the trick, trying setting the SYMPREC to a
        # specific value.
        elif current_symprec != 1e-8:
            # Set the new value
            incar["SYMPREC"] = 1e-8
            # rewrite the new INCAR file
            incar.to_file(incar_filename)
            # return the description of what we did
            return f"switched SYMPREC from {current_symprec} to 1e-8"

        # If none of the above worked, then we were not able to fix the error
        else:
            raise Exception("Unable to fix Frozen error")
