# -*- coding: utf-8 -*-

import os

import numpy

from simmate.calculators.vasp.inputs import Incar
from simmate.calculators.vasp.outputs import Oszicar
from simmate.workflow_engine import ErrorHandler


class PositiveEnergy(ErrorHandler):
    """
    Check if a run has positive absolute energy.
    If so, we trying changeing ALGO to Normal or alternatively halve the POTIM.
    """

    # run this while the VASP calculation is still going
    is_monitor = True

    def check(self, directory: str) -> bool:
        """
        Check for error in the specified directory. Note, we assume that we are
        checking the OSZICAR file. If that file is not present, we say that there
        is no error because another handler will address this.
        """

        # We check for this error in the OSZICAR because it's the smallest file
        # that will tell us energies -- and therefore the fastest to read.
        filename = os.path.join(directory, "OSZICAR")

        # check to see that the file is there first
        if os.path.exists(filename):

            # then load the file's data
            oszicar = Oszicar(filename)

            # before we check the final energy, we first need to make sure at
            # least one ionic step is present. If not, there isn't an error yet
            if not oszicar.ionic_steps:
                return False

            # the final ionic step may still not have an energy because it's
            # still going. We therefore check the most recent energy and not
            # the final energy.
            for ionic_step in reversed(oszicar.ionic_steps):
                # where ionic steps are not complete, we have numpy.NAN values
                if not numpy.isnan(ionic_step["energy_sigma_zero"]):
                    break

            # If this energy is positive, we have an error.
            if ionic_step["energy_sigma_zero"] > 0:
                return True

        # if the file doesn't exist OR if we get through our checks above, then
        # we can say there is no error.
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

        # If the current algo is *not* Normal, then switch it to that
        if current_algo != "Normal":

            # Set the new value
            incar["ALGO"] = "Normal"

            # rewrite the new INCAR file
            incar.to_file(incar_filename)

            # return the description of what we did
            return f"switched ALGO from {current_algo} to Normal"

        # if the algo is already Normal, we try reducing the POTIM by half
        else:

            # check what the current POTIM is. If it's not set, that means it's using
            # the default which is 0.5.
            current_potim = incar.get("POTIM", 0.5)

            # half the potim to try fixing the error
            new_potim = current_potim / 2.0

            # Set the new value
            incar["POTIM"] = new_potim

            # rewrite the new INCAR file
            incar.to_file(incar_filename)

            # return the description of what we did
            return f"halved POTIM from {current_potim} to {new_potim}"
