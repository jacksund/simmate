# -*- coding: utf-8 -*-


class IncorrectSmearingHandler(ErrorHandler):
    """
    Check if a calculation is a metal (zero bandgap), has been run with
    ISMEAR=-5, and is not a static calculation, which is only appropriate for
    semiconductors. If this occurs, this handler will rerun the calculation
    using the smearing settings appropriate for metals (ISMEAR=-2, SIGMA=0.2).
    """

    is_monitor = False

    def __init__(self, output_filename="vasprun.xml"):
        """
        Initializes the handler with the output file to check.
        Args:
            output_filename (str): Filename for the vasprun.xml file. Change
                this only if it is different from the default (unlikely).
        """
        self.output_filename = output_filename

    def check(self):
        """
        Check for error.
        """
        try:
            v = Vasprun(self.output_filename)
            # check whether bandgap is zero, tetrahedron smearing was used
            # and relaxation is performed.
            if (
                v.eigenvalue_band_properties[0] == 0
                and v.incar.get("ISMEAR", 1) < -3
                and v.incar.get("NSW", 0) > 1
            ):
                return True
        except Exception:
            pass
        return False

    def correct(self):
        """
        Perform corrections.
        """
        backup(VASP_BACKUP_FILES | {self.output_filename})
        vi = VaspInput.from_directory(".")

        actions = []
        actions.append({"dict": "INCAR", "action": {"_set": {"ISMEAR": 2}}})
        actions.append({"dict": "INCAR", "action": {"_set": {"SIGMA": 0.2}}})

        VaspModder(vi=vi).apply_actions(actions)
        return {"errors": ["IncorrectSmearing"], "actions": actions}
