# -*- coding: utf-8 -*-

import os

from pymatgen.io.vasp.outputs import Vasprun

from simmate.workflow_engine import ErrorHandler
from simmate.calculators.vasp.inputs import Incar


class IncorrectSmearing(ErrorHandler):
    """
    This checks if a calculation is a metal (zero bandgap), has been run with
    ISMEAR=-5, and is not a static calculation. This type of smearing is only
    appropriate for the relaxation of semiconductors and insulators -- not
    metals. If this occurs, this handler will rerun the calculation
    using the smearing settings appropriate for metals (ISMEAR=2, SIGMA=0.2).
    """

    is_monitor = False
    filename_to_check = "vasprun.xml"

    def check(self, directory: str) -> bool:

        # establish the full path to the output file
        filename = os.path.join(directory, self.filename_to_check)

        # we need this inside of a try/except clause because if the xml is
        # poorly formatted, then there is another issue at play. We only
        # want to check for the incorrect smearing here.
        try:
            # load the xml file and only parse the bare minimum
            xmlReader = Vasprun(
                filename=filename,
                parse_dos=False,
                parse_eigen=True,
                parse_projected_eigen=False,
                parse_potcar_file=False,
                exception_on_bad_xml=True,
            )

            # If all three of these conditions are met, then we have an error:
            #   (1) bandgap is zero
            #   (2) tetrahedron smearing was used (ISMEAR<-3)
            #   (3) relaxation is performed (NSW>1)
            if (
                xmlReader.eigenvalue_band_properties[0] == 0
                and xmlReader.incar.get("ISMEAR", 1) < -3
                and xmlReader.incar.get("NSW", 0) > 1
            ):
                return True

        except Exception:
            # any error above means there is some other problem, so we say
            # there is not an IncorrectSmearing error
            pass

        # if we reach this point, there is no error
        return False

    def correct(self, directory: str) -> str:

        # load the INCAR file to view the current settings
        incar_filename = os.path.join(directory, "INCAR")
        incar = Incar.from_file(incar_filename)

        # update the smearing method to one appropriate for metals
        incar["ISMEAR"] = 2
        incar["SIGMA"] = 0.2
        correction = "switched ISMEAR to 2 amd SIGMA to 0.2"

        # rewrite the INCAR with new settings
        incar.to_file(incar_filename)

        return correction
