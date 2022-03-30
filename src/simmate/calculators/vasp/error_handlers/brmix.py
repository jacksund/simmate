# -*- coding: utf-8 -*-

import os
import json

from pymatgen.io.vasp.outputs import Outcar

from simmate.workflow_engine import ErrorHandler
from simmate.calculators.vasp.inputs import Incar


class Brmix(ErrorHandler):
    """
    This handler addresses changes in charge density during a SCF loop. There are
    a series of fixes that depend on the type and state of the calculation being
    ran, so be sure to read the stages below.
    """

    is_monitor = True
    filename_to_check = "vasp.out"
    possible_error_messages = ["BRMIX: very serious problems"]

    def check(self, directory: str) -> bool:

        # load the INCAR file to view the current settings
        incar_filename = os.path.join(directory, "INCAR")
        incar = Incar.from_file(incar_filename)

        # if NELECT is in the INCAR, that means we are running
        # a charged calculation (e.g. defects). If this is the
        # case, then we want to ingore a change in electron
        # density (brmix) and move on to checking the next error.
        if "NELECT" in incar:
            return False

        # otherwise check the file as usual for the error
        return super().check(directory)

    def correct(self, directory: str) -> str:

        # load the INCAR file to view the current settings
        incar_filename = os.path.join(directory, "INCAR")
        incar = Incar.from_file(incar_filename)

        # load the error-count file if it exists
        error_count_filename = os.path.join(directory, "simmate_error_counts.json")
        if os.path.exists(error_count_filename):
            with open(error_count_filename) as error_count_file:
                error_counts = json.load(error_count_file)
        # otherwise we are starting with an empty dictionary
        else:
            error_counts = {}

        # The fix is based on the number of times we've already tried to
        # fix brmix. So let's make sure it's in our error_count dictionary.
        # If it isn't there yet, set the count to 0 and we'll update it below.
        error_counts["brmix"] = error_counts.get("brmix", 0)

        # The KGAMMA mode is relevent in a number of fixes below, so we
        # just grab that here. The default value is True.
        current_kgamma = incar.get("KGAMMA", True)

        # check if there is a valid OUTCAR
        if error_counts["brmix"] == 0:
            outcar_filename = os.path.join(directory, "OUTCAR")
            try:
                assert Outcar(outcar_filename).is_stopped is False
            except Exception:
                # if the OUTCAR isn't valid, we want to skip the first attempted
                # correction below. We do this by adding 1 to our error count.
                error_counts["brmix"] += 1

        # we don't return the correction immediately because we need to rewrite some
        # files below first. Therefore we just store the correction as a variable.

        if error_counts["brmix"] == 0:
            # If the OUTCAR is valid - simply rerun the job and increment
            # error count for next time.
            incar["ISTART"] = 1
            correction = "switched ISTART to 1"
            error_counts["brmix"] += 1

        elif error_counts["brmix"] == 1:
            # Use Kerker mixing w/default values for other parameters
            incar["IMIX"] = 1
            correction = "switched IMIX to 1"
            error_counts["brmix"] += 1

        elif error_counts["brmix"] == 2 and current_kgamma == True:
            # switch to Monkhorst and turn off Kerker mixing (IMIX=1)
            incar["KGAMMA"] = False
            incar.pop("IMIX", None)
            correction = "removed any IMIX tag and switched KGAMMA to False"
            error_counts["brmix"] += 1

        elif error_counts["brmix"] in [2, 3] and current_kgamma == False:
            # switch to Gamma and turn off Kerker mixing (IMIX=1)
            incar["KGAMMA"] = True
            incar.pop("IMIX", None)
            correction = "removed any IMIX tag and switched KGAMMA to True"
            error_counts["brmix"] += 1

            # TODO: I'm not sure what Custodian did here, so I haven't adapted
            # it yet. How can the number of kpoints be less than 1...?
            #
            # if vi["KPOINTS"].num_kpts < 1:
            #     all_kpts_even = all(bool(n % 2 == 0) for n in vi["KPOINTS"].kpts[0])
            #     if all_kpts_even:
            #         new_kpts = (tuple(n + 1 for n in vi["KPOINTS"].kpts[0]),)
            #         actions.append(
            #             {
            #                 "dict": "KPOINTS",
            #                 "action": {"_set": {"kpoints": new_kpts}},
            #             }
            #         )

        else:

            # Try turning off symmetry and using a Gamma-packed grid
            incar["ISYM"] = 0
            incar["KGAMMA"] = True
            correction = "switched ISYM to 0 and KGAMMA to True"

            # Check the current ICHARG setting, where default is 0
            # If the ICHARG is less than 10, then we want to delete the CHGCAR
            # and WAVECAR to ensure the next run is a clean start.
            current_icharg = incar.get("ICHARG", 0)
            if current_icharg < 10:
                os.remove(os.path.join(directory, "CHGCAR"))
                os.remove(os.path.join(directory, "WAVECAR"))
                correction += " and deleted CHGCAR and WAVECAR"
            # BUG: why doesn't custodian add an attempt here?
            # error_counts["brmix"] += 1

        # rewrite the INCAR with new settings
        incar.to_file(incar_filename)

        # rewrite the new error count file
        with open(error_count_filename, "w") as file:
            json.dump(error_counts, file)

        # now return the correction made for logging
        return correction
