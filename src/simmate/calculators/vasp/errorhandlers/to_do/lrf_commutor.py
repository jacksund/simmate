# -*- coding: utf-8 -*-


class LrfCommutatorHandler(ErrorHandler):
    """
    Corrects LRF_COMMUTATOR errors by setting LPEAD=True if not already set.
    Note that switching LPEAD=T can slightly change results versus the
    default due to numerical evaluation of derivatives.
    """

    is_monitor = True

    error_msgs = {"lrf_comm": ["LRF_COMMUTATOR internal error"]}

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
                for err, msgs in LrfCommutatorHandler.error_msgs.items():
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

        if "lrf_comm" in self.errors:
            if Outcar(zpath(os.path.join(os.getcwd(), "OUTCAR"))).is_stopped is False:
                if not vi["INCAR"].get("LPEAD"):
                    actions.append(
                        {"dict": "INCAR", "action": {"_set": {"LPEAD": True}}}
                    )

        VaspModder(vi=vi).apply_actions(actions)
        return {"errors": list(self.errors), "actions": actions}
