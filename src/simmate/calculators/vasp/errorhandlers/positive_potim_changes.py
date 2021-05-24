# -*- coding: utf-8 -*-

class PotimErrorHandler(ErrorHandler):
    """
    Check if a run has excessively large positive energy changes.
    This is typically caused by too large a POTIM. Runs typically
    end up crashing with some other error (e.g. BRMIX) as the geometry
    gets progressively worse.
    """

    is_monitor = True

    def __init__(self, input_filename="POSCAR", output_filename="OSZICAR", dE_threshold=1):
        """
        Initializes the handler with the input and output files to check.
        Args:
            input_filename (str): This is the POSCAR file that the run
                started from. Defaults to "POSCAR". Change
                this only if it is different from the default (unlikely).
            output_filename (str): This is the OSZICAR file. Change
                this only if it is different from the default (unlikely).
            dE_threshold (float): The threshold energy change. Defaults to 1eV.
        """
        self.input_filename = input_filename
        self.output_filename = output_filename
        self.dE_threshold = dE_threshold

    def check(self):
        """
        Check for error.
        """
        try:
            oszicar = Oszicar(self.output_filename)
            n = len(Poscar.from_file(self.input_filename).structure)
            max_dE = max([s["dE"] for s in oszicar.ionic_steps[1:]]) / n
            if max_dE > self.dE_threshold:
                return True
        except Exception:
            return False
        return None

    def correct(self):
        """
        Perform corrections.
        """
        backup(VASP_BACKUP_FILES)
        vi = VaspInput.from_directory(".")
        potim = float(vi["INCAR"].get("POTIM", 0.5))
        ibrion = int(vi["INCAR"].get("IBRION", 0))
        if potim < 0.2 and ibrion != 3:
            actions = [{"dict": "INCAR", "action": {"_set": {"IBRION": 3, "SMASS": 0.75}}}]
        elif potim < 0.1:
            actions = [{"dict": "INCAR", "action": {"_set": {"SYMPREC": 1e-8}}}]
        else:
            actions = [{"dict": "INCAR", "action": {"_set": {"POTIM": potim * 0.5}}}]

        VaspModder(vi=vi).apply_actions(actions)
        return {"errors": ["POTIM"], "actions": actions}