# -*- coding: utf-8 -*-


class StdErrHandler(ErrorHandler):
    """
    Master StdErr class that handles a number of common errors
    that occur during VASP runs with error messages only in
    the standard error.
    """

    is_monitor = True

    error_msgs = {
        "kpoints_trans": [
            "internal error in GENERATE_KPOINTS_TRANS: "
            "number of G-vector changed in star"
        ],
        "out_of_memory": ["Allocation would exceed memory limit"],
    }

    def __init__(self, output_filename="std_err.txt"):
        """
        Initializes the handler with the output file to check.
        Args:
            output_filename (str): This is the file where the stderr for vasp
                is being redirected. The error messages that are checked are
                present in the stderr. Defaults to "std_err.txt", which is the
                default redirect used by :class:`custodian.vasp.jobs.VaspJob`.
        """
        self.output_filename = output_filename
        self.errors = set()
        self.error_count = Counter()

    def check(self):
        """
        Check for error.
        """
        self.errors = set()
        with open(self.output_filename, "r") as f:
            for line in f:
                l = line.strip()
                for err, msgs in StdErrHandler.error_msgs.items():
                    for msg in msgs:
                        if l.find(msg) != -1:
                            self.errors.add(err)
        return len(self.errors) > 0

    def correct(self):
        """
        Perform corrections.
        """
        backup(VASP_BACKUP_FILES | {self.output_filename})
        actions = []
        vi = VaspInput.from_directory(".")

        if "kpoints_trans" in self.errors:
            if self.error_count["kpoints_trans"] == 0:
                m = reduce(operator.mul, vi["KPOINTS"].kpts[0])
                m = max(int(round(m ** (1 / 3))), 1)
                if vi["KPOINTS"].style.name.lower().startswith("m"):
                    m += m % 2
                actions.append(
                    {"dict": "KPOINTS", "action": {"_set": {"kpoints": [[m] * 3]}}}
                )
                self.error_count["kpoints_trans"] += 1

        if "out_of_memory" in self.errors:
            if vi["INCAR"].get("KPAR", 1) > 1:
                reduced_kpar = max(vi["INCAR"].get("KPAR", 1) // 2, 1)
                actions.append(
                    {"dict": "INCAR", "action": {"_set": {"KPAR": reduced_kpar}}}
                )

        VaspModder(vi=vi).apply_actions(actions)
        return {"errors": list(self.errors), "actions": actions}
