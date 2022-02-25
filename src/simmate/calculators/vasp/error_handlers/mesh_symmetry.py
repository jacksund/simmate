# -*- coding: utf-8 -*-

import os

from pymatgen.io.vasp.outputs import Vasprun
from pymatgen.io.vasp.inputs import Kpoints

from simmate.workflow_engine import ErrorHandler
from simmate.calculators.vasp.inputs import Incar


class MeshSymmetry(ErrorHandler):
    """
    Corrects the mesh symmetry error in VASP. This error is sometimes
    non-fatal and the job can complete successfully. So this error handler
    only checks at the end of the run, and if the run has converged, no error
    is recorded. We can also ignore this error if symmetry is turned off or if
    automatic k-mesh has been used.
    """

    is_monitor = False
    filename_to_check = "vasp.out"
    possible_error_messages = [
        "Reciprocal lattice and k-lattice belong to different class of"
    ]

    def check(self, directory: str) -> bool:

        # load the INCAR file to view the current settings
        incar_filename = os.path.join(directory, "INCAR")
        incar = Incar.from_file(incar_filename)

        # check if there is a KPOINTS file and if so, read it and check the
        # kpoint style being using.
        kpoints_filename = os.path.join(directory, "KPOINTS")
        if os.path.exists(kpoints_filename):
            kpoints = Kpoints.from_file(kpoints_filename)
            kpoints_style = kpoints.style
        else:
            kpoints_style = None

        # We can say there is no error if one of the following is true:
        #   (1) symmetry is turned off
        #   (2) KSPACING is used
        #   (3) KPOINTS file uses and "Automatic" mesh
        if (
            incar.get("ISYM", 1) == 0
            or incar.get("KSPACING")
            or kpoints_style == Kpoints.supported_modes.Automatic
        ):
            return False

        # Now check if the calculation converged. If it did, we ignore the error.
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
            if xmlReader.converged:
                return False
        except Exception:
            pass

        # Finally, we can now search for the error message. We can use the parent
        # class's default function to do this.
        return super().check(directory)

    def correct(self, directory: str) -> str:

        raise NotImplementedError(
            "The fix for MeshSymmetryError hasn't been converted from Custodian "
            "to Simmate yet. A fix does exist though, so be sure to tell our "
            "that team you need it!"
        )

        # load the INCAR file to view the current settings
        kpoints_filename = os.path.join(directory, "KPOINTS")
        kpoints = Kpoints.from_file(kpoints_filename)

        # !!! I'm not sure what Custodian is doing here exactly, so I need to
        # revisit this when I have my KPOINTS class implemented

        # from functools import reduce
        # import operator
        # backup(VASP_BACKUP_FILES | {self.output_filename})
        # vi = VaspInput.from_directory(".")
        # m = reduce(operator.mul, vi["KPOINTS"].kpts[0])
        # m = max(int(round(m ** (1 / 3))), 1)
        # if vi["KPOINTS"].style.name.lower().startswith("m"):
        #     m += m % 2
        # actions = [{"dict": "KPOINTS", "action": {"_set": {"kpoints": [[m] * 3]}}}]
        # VaspModder(vi=vi).apply_actions(actions)
        # return {"errors": ["mesh_symmetry"], "actions": actions}
