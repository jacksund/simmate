# -*- coding: utf-8 -*-


class UnconvergedErrorHandler(ErrorHandler):
    """
    Check if a run is converged.
    """

    is_monitor = False

    def __init__(self, output_filename="vasprun.xml"):
        """
        Initializes the handler with the output file to check.
        Args:
            output_vasprun (str): Filename for the vasprun.xml file. Change
                this only if it is different from the default (unlikely).
        """
        self.output_filename = output_filename

    def check(self):
        """
        Check for error.
        """
        try:
            v = Vasprun(self.output_filename)
            if not v.converged:
                return True
        except Exception:
            pass
        return False

    def correct(self):
        """
        Perform corrections.
        """
        v = Vasprun(self.output_filename)
        actions = []
        if not v.converged_electronic:
            # Ladder from VeryFast to Fast to Fast to All
            # These progressively switches to more stable but more
            # expensive algorithms
            algo = v.incar.get("ALGO", "Normal")
            if algo == "VeryFast":
                actions.append({"dict": "INCAR", "action": {"_set": {"ALGO": "Fast"}}})
            elif algo == "Fast":
                actions.append(
                    {"dict": "INCAR", "action": {"_set": {"ALGO": "Normal"}}}
                )
            elif algo == "Normal":
                actions.append({"dict": "INCAR", "action": {"_set": {"ALGO": "All"}}})
            else:
                # Try mixing as last resort
                new_settings = {
                    "ISTART": 1,
                    "ALGO": "Normal",
                    "NELMDL": -6,
                    "BMIX": 0.001,
                    "AMIX_MAG": 0.8,
                    "BMIX_MAG": 0.001,
                }

                if not all(
                    v.incar.get(k, "") == val for k, val in new_settings.items()
                ):
                    actions.append({"dict": "INCAR", "action": {"_set": new_settings}})

        elif not v.converged_ionic:
            # Just continue optimizing and let other handles fix ionic
            # optimizer parameters
            actions.append({"dict": "INCAR", "action": {"_set": {"IBRION": 1}}})
            actions.append(
                {"file": "CONTCAR", "action": {"_file_copy": {"dest": "POSCAR"}}}
            )

        if actions:
            vi = VaspInput.from_directory(".")
            backup(VASP_BACKUP_FILES)
            VaspModder(vi=vi).apply_actions(actions)
            return {"errors": ["Unconverged"], "actions": actions}

        # Unfixable error. Just return None for actions.
        return {"errors": ["Unconverged"], "actions": None}
