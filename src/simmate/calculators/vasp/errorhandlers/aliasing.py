# -*- coding: utf-8 -*-

class AliasingErrorHandler(ErrorHandler):
    """
    Master VaspErrorHandler class that handles a number of common errors
    that occur during VASP runs.
    """

    is_monitor = True

    error_msgs = {
        "aliasing": ["WARNING: small aliasing (wrap around) errors must be expected"],
        "aliasing_incar": ["Your FFT grids (NGX,NGY,NGZ) are not sufficient " "for an accurate"],
    }

    def __init__(self, output_filename="vasp.out"):
        """
        Initializes the handler with the output file to check.
        Args:
            output_filename (str): This is the file where the stdout for vasp
                is being redirected. The error messages that are checked are
                present in the stdout. Defaults to "vasp.out", which is the
                default redirect used by :class:`custodian.vasp.jobs.VaspJob`.
        """
        self.output_filename = output_filename
        self.errors = set()

    def check(self):
        """
        Check for error.
        """
        incar = Incar.from_file("INCAR")
        self.errors = set()
        with open(self.output_filename, "r") as f:
            for line in f:
                l = line.strip()
                for err, msgs in AliasingErrorHandler.error_msgs.items():
                    for msg in msgs:
                        if l.find(msg) != -1:
                            # this checks if we want to run a charged
                            # computation (e.g., defects) if yes we don't
                            # want to kill it because there is a change in e-
                            # density (brmix error)
                            if err == "brmix" and "NELECT" in incar:
                                continue
                            self.errors.add(err)
        return len(self.errors) > 0

    def correct(self):
        """
        Perform corrections.
        """
        backup(VASP_BACKUP_FILES | {self.output_filename})
        actions = []
        vi = VaspInput.from_directory(".")

        if "aliasing" in self.errors:
            with open("OUTCAR") as f:
                grid_adjusted = False
                changes_dict = {}
                r = re.compile(r".+aliasing errors.*(NG.)\s*to\s*(\d+)")
                for line in f:
                    m = r.match(line)
                    if m:
                        changes_dict[m.group(1)] = int(m.group(2))
                        grid_adjusted = True
                    # Ensure that all NGX, NGY, NGZ have been checked
                    if grid_adjusted and "NGZ" in line:
                        actions.append({"dict": "INCAR", "action": {"_set": changes_dict}})
                        if vi["INCAR"].get("ICHARG", 0) < 10:
                            actions.extend(
                                [
                                    {
                                        "file": "CHGCAR",
                                        "action": {"_file_delete": {"mode": "actual"}},
                                    },
                                    {
                                        "file": "WAVECAR",
                                        "action": {"_file_delete": {"mode": "actual"}},
                                    },
                                ]
                            )
                        break

        if "aliasing_incar" in self.errors:
            # vasp seems to give different warnings depending on whether the
            # aliasing error was caused by user supplied inputs
            d = {k: 1 for k in ["NGX", "NGY", "NGZ"] if k in vi["INCAR"].keys()}
            actions.append({"dict": "INCAR", "action": {"_unset": d}})

            if vi["INCAR"].get("ICHARG", 0) < 10:
                actions.extend(
                    [
                        {
                            "file": "CHGCAR",
                            "action": {"_file_delete": {"mode": "actual"}},
                        },
                        {
                            "file": "WAVECAR",
                            "action": {"_file_delete": {"mode": "actual"}},
                        },
                    ]
                )

        VaspModder(vi=vi).apply_actions(actions)
        return {"errors": list(self.errors), "actions": actions}