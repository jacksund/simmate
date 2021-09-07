# -*- coding: utf-8 -*-


class DriftErrorHandler(ErrorHandler):
    """
    Corrects for total drift exceeding the force convergence criteria.
    """

    def __init__(self, max_drift=None, to_average=3, enaug_multiply=2):
        """
        Initializes the handler with max drift
        Args:
            max_drift (float): This defines the max drift. Leaving this at the default of None gets the max_drift from
                EDFIFFG
        """

        self.max_drift = max_drift
        self.to_average = int(to_average)
        self.enaug_multiply = enaug_multiply

    def check(self):
        """
        Check for error.
        """
        incar = Incar.from_file("INCAR")
        if incar.get("EDIFFG", 0.1) >= 0 or incar.get("NSW", 0) == 0:
            # Only activate when force relaxing and ionic steps
            # NSW check prevents accidental effects when running DFPT
            return False

        if not self.max_drift:
            self.max_drift = incar["EDIFFG"] * -1

        try:
            outcar = Outcar("OUTCAR")
        except Exception:
            # Can't perform check if Outcar not valid
            return False

        if len(outcar.data.get("drift", [])) < self.to_average:
            # Ensure enough steps to get average drift
            return False

        curr_drift = outcar.data.get("drift", [])[::-1][: self.to_average]
        curr_drift = np.average([np.linalg.norm(d) for d in curr_drift])
        return curr_drift > self.max_drift

    def correct(self):
        """
        Perform corrections.
        """
        backup(VASP_BACKUP_FILES)
        actions = []
        vi = VaspInput.from_directory(".")

        incar = vi["INCAR"]
        outcar = Outcar("OUTCAR")

        # Move CONTCAR to POSCAR
        actions.append(
            {"file": "CONTCAR", "action": {"_file_copy": {"dest": "POSCAR"}}}
        )

        # First try adding ADDGRID
        if not incar.get("ADDGRID", False):
            actions.append({"dict": "INCAR", "action": {"_set": {"ADDGRID": True}}})
        # Otherwise set PREC to High so ENAUG can be used to control Augmentation Grid Size
        elif incar.get("PREC", "Accurate").lower() != "high":
            actions.append({"dict": "INCAR", "action": {"_set": {"PREC": "High"}}})
            actions.append(
                {
                    "dict": "INCAR",
                    "action": {"_set": {"ENAUG": incar.get("ENCUT", 520) * 2}},
                }
            )
        # PREC is already high and ENAUG set so just increase it
        else:
            actions.append(
                {
                    "dict": "INCAR",
                    "action": {
                        "_set": {
                            "ENAUG": int(incar.get("ENAUG", 1040) * self.enaug_multiply)
                        }
                    },
                }
            )

        curr_drift = outcar.data.get("drift", [])[::-1][: self.to_average]
        curr_drift = np.average([np.linalg.norm(d) for d in curr_drift])
        VaspModder(vi=vi).apply_actions(actions)
        return {
            "errors": "Excessive drift {} > {}".format(curr_drift, self.max_drift),
            "actions": actions,
        }
