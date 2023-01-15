# -*- coding: utf-8 -*-


class ScanMetalHandler(ErrorHandler):
    """
    Check if a SCAN calculation is a metal (zero bandgap) but has been run with
    a KSPACING value appropriate for semiconductors. If this occurs, this handler
    will rerun the calculation using the KSPACING setting appropriate for metals
    (KSPACING=0.22). Note that this handler depends on values set in MPScanRelaxSet.
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
            # check whether bandgap is zero and tetrahedron smearing was used
            if (
                v.eigenvalue_band_properties[0] == 0
                and v.incar.get("KSPACING", 1) > 0.22
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

        _dummy_structure = Structure(
            [1, 0, 0, 0, 1, 0, 0, 0, 1],
            ["I"],
            [[0, 0, 0]],
        )
        new_vis = MPScanRelaxSet(_dummy_structure, bandgap=0)

        actions = []
        actions.append(
            {
                "dict": "INCAR",
                "action": {"_set": {"KSPACING": new_vis.incar["KSPACING"]}},
            }
        )

        VaspModder(vi=vi).apply_actions(actions)
        return {"errors": ["ScanMetal"], "actions": actions}
