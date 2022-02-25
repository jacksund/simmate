# -*- coding: utf-8 -*-

import os

from simmate.calculators.vasp.inputs import Incar
from simmate.calculators.vasp.outputs import Oszicar
from simmate.workflow_engine import ErrorHandler


class NonConverging(ErrorHandler):
    """
    If a run is hitting the maximum number of electronic steps for a significant
    number of ionic steps (i.e. 10), then we consider the job to be nonconverging
    and in error. To try fixing this, we switch the ALGO to Normal.
    """

    is_monitor = True

    def __init__(self, min_ionic_steps: int = 10):
        self.min_ionic_steps = min_ionic_steps

    def check(self, directory: str) -> bool:
        """
        Check for error in the specified directory. Note, we assume that we are
        checking the OSZICAR file. If that file is not present, we say that there
        is no error because another handler will address this.
        """

        # We check for this error in the OSZICAR because it's the smallest file
        # that will tell us energies -- and therefore the fastest to read.
        oszicar_filename = os.path.join(directory, "OSZICAR")
        # we also need the INCAR for this error handler
        incar_filename = os.path.join(directory, "INCAR")

        # check to see that the files are there first
        if os.path.exists(oszicar_filename) and os.path.exists(incar_filename):

            # then load each file's data
            oszicar = Oszicar(oszicar_filename)
            incar = Incar.from_file(incar_filename)

            # check what the current NELM is. If it's not set, that means it's using
            # the default which is 60. This is the max SCF steps allowed.
            current_nelm = incar.get("NELM", 60)

            # now let's go through the oszicar data
            # First, check if we have the minmimum number of ionic steps completed
            # for us to even consider this error. If not, there's no error yet
            if len(oszicar.ionic_steps) < self.min_ionic_steps:
                return False

            # if there are enough ionic_steps, let's look at the most N recent ones
            # where N is our min_ionic_steps. If all of these have electronic steps
            # equal to the NELM (so the maximum allowed), then we are having convergence
            # issues and the error exists. Note we ignore the final ionic step because
            # it may not be complete yet.
            for ionic_step in oszicar.ionic_steps[-1 * self.min_ionic_steps : -1]:

                # As soon as we find one ionic step that converged before the
                # NELM limit, we can say the error is not present and exit
                if len(ionic_step["electronic_steps"]) != current_nelm:
                    return False

            # if we get through the entire for-loop above without exiting, then
            # that means all recent ionic_steps hit the maximum electronic steps
            # every time and the error is present!
            return True

        # if the files don't exist, we are not seeing any error yet
        return False

    def correct(self, directory: str) -> str:
        """
        Perform corrections based on the INCAR.
        """
        # Note "error" here is just True because there is no variation in this ErrorHandler.
        # This value isn't used in fixing the Error anyways.

        # load the INCAR file to view the current settings
        incar_filename = os.path.join(directory, "INCAR")
        incar = Incar.from_file(incar_filename)

        # check what the current ALGO is. If it's not set, that means it's using
        # the default which is "Normal".
        current_algo = incar.get("ALGO", "Normal")
        # also check mixing parameters
        current_amix = incar.get("AMIX", 0.4)
        current_bmix = incar.get("BMIX", 1.0)
        current_amin = incar.get("AMIN", 0.1)

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

        # try linear mixing
        elif current_amix > 0.1 and current_bmix > 0.01:
            # Set the new values
            new_settings = {"AMIX": 0.1, "BMIX": 0.01, "ICHARG": 2}
            incar.update(new_settings)
            # rewrite the new INCAR file
            incar.to_file(incar_filename)
            # return the description of what we did
            return f"switched linear mixing via {new_settings}"

        # try increasing bmix
        elif current_bmix < 3.0 and current_amin > 0.01:
            # Set the new values
            new_settings = {"AMIN": 0.01, "BMIX": 3.0, "ICHARG": 2}
            incar.update(new_settings)
            # rewrite the new INCAR file
            incar.to_file(incar_filename)
            # return the description of what we did
            return f"switched linear mixing via {new_settings}"

        # If none of the above worked, then we were not able to fix the error
        else:
            raise Exception("Unable to fix NonConverging error")
