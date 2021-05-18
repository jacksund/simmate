# -*- coding: utf-8 -*-

class MeshSymmetryErrorHandler(ErrorHandler):
    """
    Corrects the mesh symmetry error in VASP. This error is sometimes
    non-fatal. So this error handler only checks at the end of the run,
    and if the run has converged, no error is recorded.
    """

    is_monitor = False

    def __init__(self, output_filename="vasp.out", output_vasprun="vasprun.xml"):
        """
        Initializes the handler with the output files to check.
        Args:
            output_filename (str): This is the file where the stdout for vasp
                is being redirected. The error messages that are checked are
                present in the stdout. Defaults to "vasp.out", which is the
                default redirect used by :class:`custodian.vasp.jobs.VaspJob`.
            output_vasprun (str): Filename for the vasprun.xml file. Change
                this only if it is different from the default (unlikely).
        """
        self.output_filename = output_filename
        self.output_vasprun = output_vasprun

    def check(self):
        """
        Check for error.
        """
        msg = "Reciprocal lattice and k-lattice belong to different class of" " lattices."

        vi = VaspInput.from_directory(".")
        # disregard this error if KSPACING is set and no KPOINTS file is generated
        if vi["INCAR"].get("KSPACING", False):
            return False

        # According to VASP admins, you can disregard this error
        # if symmetry is off
        # Also disregard if automatic KPOINT generation is used
        if (not vi["INCAR"].get("ISYM", True)) or vi["KPOINTS"].style == Kpoints.supported_modes.Automatic:
            return False

        try:
            v = Vasprun(self.output_vasprun)
            if v.converged:
                return False
        except Exception:
            pass
        with open(self.output_filename, "r") as f:
            for line in f:
                l = line.strip()
                if l.find(msg) != -1:
                    return True
        return False

    def correct(self):
        """
        Perform corrections.
        """
        backup(VASP_BACKUP_FILES | {self.output_filename})
        vi = VaspInput.from_directory(".")
        m = reduce(operator.mul, vi["KPOINTS"].kpts[0])
        m = max(int(round(m ** (1 / 3))), 1)
        if vi["KPOINTS"].style.name.lower().startswith("m"):
            m += m % 2
        actions = [{"dict": "KPOINTS", "action": {"_set": {"kpoints": [[m] * 3]}}}]
        VaspModder(vi=vi).apply_actions(actions)
        return {"errors": ["mesh_symmetry"], "actions": actions}