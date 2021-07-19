# -*- coding: utf-8 -*-

class LargeSigmaHandler(ErrorHandler):
    """
    When ISMEAR > 0 (Gaussian or Methfessel-Paxton), monitor the magnitude of the entropy
    term T*S in the OUTCAR file. If the entropy term is larger than 1 meV/atom, reduce the
    value of SIGMA. See VASP documentation for ISMEAR.
    """

    is_monitor = True

    def __init__(self):
        """
        Initializes the handler with a buffer time.
        """

    def check(self):
        """
        Check for error.
        """
        incar = Incar.from_file("INCAR")
        try:
            outcar = Outcar("OUTCAR")
        except Exception:
            # Can't perform check if Outcar not valid
            return False

        if incar.get("ISMEAR", 0) > 0:
            # Read the latest entropy term.
            outcar.read_pattern(
                {"entropy": r"entropy T\*S.*= *(\D\d*\.\d*)"}, postprocess=float, reverse=True, terminate_on_match=True
            )
            n_atoms = Structure.from_file("POSCAR").num_sites
            if outcar.data.get("entropy", []):
                entropy_per_atom = abs(np.max(outcar.data.get("entropy"))) / n_atoms

                # if more than 1 meV/atom, reduce sigma
                if entropy_per_atom > 0.001:
                    return True

        return False

    def correct(self):
        """
        Perform corrections.
        """
        backup(VASP_BACKUP_FILES)
        actions = []
        vi = VaspInput.from_directory(".")
        sigma = vi["INCAR"].get("SIGMA", 0.2)

        # Reduce SIGMA by 0.06 if larger than 0.08
        # this will reduce SIGMA from the default of 0.2 to the practical
        # minimum value of 0.02 in 3 steps
        if sigma > 0.08:
            actions.append(
                {
                    "dict": "INCAR",
                    "action": {"_set": {"SIGMA": sigma - 0.06}},
                }
            )

        VaspModder(vi=vi).apply_actions(actions)
        return {"errors": ["LargeSigma"], "actions": actions}
