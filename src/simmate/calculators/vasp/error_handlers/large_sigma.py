# -*- coding: utf-8 -*-

import os

from simmate.toolkit import Structure
from simmate.workflow_engine import ErrorHandler
from simmate.calculators.vasp.inputs import Incar


class LargeSigma(ErrorHandler):
    """
    When ISMEAR >= 0 (Gaussian or Methfessel-Paxton), we need to monitor the
    magnitude of the entropy term T*S. If the entropy term is larger than
    1 meV/atom, then we reduce value of SIGMA. See VASP documentation for ISMEAR.
    """

    is_monitor = True

    def __init__(self, entropy_per_atom_threshold=0.001):
        self.entropy_per_atom_threshold = entropy_per_atom_threshold

    def check(self, directory: str) -> bool:

        # load the INCAR file to view the current settings
        incar_filename = os.path.join(directory, "INCAR")
        incar = Incar.from_file(incar_filename)

        # this error is only relevent if we have ISMEAR >= 0. So we return that
        # there is no error otherwise.
        if incar.get("ISMEAR", -1) < 0:
            return False

        # We check for this error in the OUTCAR
        # TODO: I don't have an OUTCAR class written yet so I just read the
        # raw text and search for the entropy information directly
        outcar_filename = os.path.join(directory, "OUTCAR")

        # check to see that the file is there first
        if os.path.exists(outcar_filename):

            # read the file content and then close it
            with open(outcar_filename) as file:
                outcar_lines = file.readlines()

            # also load the structure so we know how many sites there are
            poscar_filename = os.path.join(directory, "POSCAR")
            structure = Structure.from_file(poscar_filename)
            nsites = structure.num_sites

            # iterate through all the lines and look for the entropy value.
            # these lines look like this:
            #   entropy T*S    EENTRO =         0.00000000
            # where the entropy is the final value. If any entropy value
            # exceeds our threshold then we have an error!
            for line in outcar_lines:
                if "entropy T*S" in line:
                    entropy = float(line.split()[-1])
                    entropy_per_atom = entropy / nsites
                    if entropy_per_atom > self.entropy_per_atom_threshold:
                        return True

        # if the file doesn't exist OR the threshold is never hit, the we are
        # not seeing any error.
        return False

    def correct(self, directory: str) -> str:

        # load the INCAR file to view the current settings
        incar_filename = os.path.join(directory, "INCAR")
        incar = Incar.from_file(incar_filename)

        # grab the sigma value being used where the default is 0.2
        current_sigma = incar.get("SIGMA", 0.2)

        # If the sigma value is above 0.08, we try reducing it by 0.06.
        # Note the .00001 added on is to handle rounding issues
        if current_sigma > 0.08001:
            new_sigma = current_sigma - 0.06
            incar["SIGMA"] = new_sigma
            incar.to_file(incar_filename)
            return f"reduced SIGMA from {current_sigma} to {new_sigma}"

        # check what the current KSPACING is. If it's not set, that means it's using
        # the default which is 0.5.
        current_kspacing = incar.get("KSPACING", 0.5)

        # If the sigma value is at or below 0.08 and we still have this error,
        # we may not have a dense enough kpt mesh. We then try decreasing KSPACING
        # by 20% in each direction. which approximately doubles the number
        # of kpoints. We stop trying this if we are below a K-pt density of 0.3
        if current_kspacing > 0.3:
            new_kspacing = current_kspacing * 0.8
            incar["KSPACING"] = new_kspacing
            # rewrite the INCAR with new settings
            incar.to_file(incar_filename)
            return f"switched KSPACING from {current_kspacing} to {new_kspacing}"

        # otherwise we can't do anything else and should flag the calculation
        # as failed
        raise Exception("Unable to fix LargeSigma error")
