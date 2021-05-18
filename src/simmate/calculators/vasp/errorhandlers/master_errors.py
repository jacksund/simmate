# -*- coding: utf-8 -*-

class VaspErrorHandler(ErrorHandler):
    """
    Master VaspErrorHandler class that handles a number of common errors
    that occur during VASP runs.
    """

    is_monitor = True

    error_msgs = {
        "tet": [
            "Tetrahedron method fails",
            "Fatal error detecting k-mesh",
            "Fatal error: unable to match k-point",
            "Routine TETIRR needs special values",
            "Tetrahedron method fails (number of k-points < 4)",
            "BZINTS",
        ],
        "inv_rot_mat": ["rotation matrix was not found (increase " "SYMPREC)"],
        "brmix": ["BRMIX: very serious problems"],
        "subspacematrix": ["WARNING: Sub-Space-Matrix is not hermitian in " "DAV"],
        "tetirr": ["Routine TETIRR needs special values"],
        "incorrect_shift": ["Could not get correct shifts"],
        "real_optlay": ["REAL_OPTLAY: internal error", "REAL_OPT: internal ERROR"],
        "rspher": ["ERROR RSPHER"],
        "dentet": ["DENTET"],
        "too_few_bands": ["TOO FEW BANDS"],
        "triple_product": ["ERROR: the triple product of the basis vectors"],
        "rot_matrix": ["Found some non-integer element in rotation matrix", "SGRCON"],
        "brions": ["BRIONS problems: POTIM should be increased"],
        "pricel": ["internal error in subroutine PRICEL"],
        "zpotrf": ["LAPACK: Routine ZPOTRF failed"],
        "amin": ["One of the lattice vectors is very long (>50 A), but AMIN"],
        "zbrent": ["ZBRENT: fatal internal in", "ZBRENT: fatal error in bracketing"],
        "pssyevx": ["ERROR in subspace rotation PSSYEVX"],
        "eddrmm": ["WARNING in EDDRMM: call to ZHEGV failed"],
        "edddav": ["Error EDDDAV: Call to ZHEGV failed"],
        "grad_not_orth": ["EDWAV: internal error, the gradient is not orthogonal"],
        "nicht_konv": ["ERROR: SBESSELITER : nicht konvergent"],
        "zheev": ["ERROR EDDIAG: Call to routine ZHEEV failed!"],
        "elf_kpar": ["ELF: KPAR>1 not implemented"],
        "elf_ncl": ["WARNING: ELF not implemented for non collinear case"],
        "rhosyg": ["RHOSYG"],
        "posmap": ["POSMAP"],
        "point_group": ["group operation missing"],
        "symprec_noise": ["determination of the symmetry of your systems shows a strong"],
    }

    def __init__(
        self,
        output_filename="vasp.out",
        natoms_large_cell=100,
        errors_subset_to_catch=None,
    ):
        """
        Initializes the handler with the output file to check.
        Args:
            output_filename (str): This is the file where the stdout for vasp
                is being redirected. The error messages that are checked are
                present in the stdout. Defaults to "vasp.out", which is the
                default redirect used by :class:`custodian.vasp.jobs.VaspJob`.
            natoms_large_cell (int): Number of atoms threshold to treat cell
                as large. Affects the correction of certain errors. Defaults to
                100.
            errors_subset_to_detect (list): A subset of errors to catch. The
                default is None, which means all supported errors are detected.
                Use this to only catch only a subset of supported errors.
                E.g., ["eddrrm", "zheev"] will only catch the eddrmm and zheev
                errors, and not others. If you wish to only excluded one or
                two of the errors, you can create this list by the following
                lines:
                ```
                subset = list(VaspErrorHandler.error_msgs.keys())
                subset.pop("eddrrm")
                handler = VaspErrorHandler(errors_subset_to_catch=subset)
                ```
        """
        self.output_filename = output_filename
        self.errors = set()
        self.error_count = Counter()
        # threshold of number of atoms to treat the cell as large.
        self.natoms_large_cell = natoms_large_cell
        self.errors_subset_to_catch = errors_subset_to_catch or list(VaspErrorHandler.error_msgs.keys())
        self.logger = logging.getLogger(self.__class__.__name__)

    def check(self):
        """
        Check for error.
        """
        incar = Incar.from_file("INCAR")
        self.errors = set()
        error_msgs = set()
        with open(self.output_filename, "r") as f:
            for line in f:
                l = line.strip()
                for err, msgs in VaspErrorHandler.error_msgs.items():
                    if err in self.errors_subset_to_catch:
                        for msg in msgs:
                            if l.find(msg) != -1:
                                # this checks if we want to run a charged
                                # computation (e.g., defects) if yes we don't
                                # want to kill it because there is a change in
                                # e-density (brmix error)
                                if err == "brmix" and "NELECT" in incar:
                                    continue
                                self.errors.add(err)
                                error_msgs.add(msg)
        for msg in error_msgs:
            self.logger.error(msg, extra={"incar": incar.as_dict()})
        return len(self.errors) > 0

    def correct(self):
        """
        Perform corrections.
        """
        backup(VASP_BACKUP_FILES | {self.output_filename})
        actions = []
        vi = VaspInput.from_directory(".")

        if self.errors.intersection(["tet", "dentet"]):
            if vi["INCAR"].get("KSPACING"):
                # decrease KSPACING by 20% in each direction (approximately double no. of kpoints)
                actions.append(
                    {
                        "dict": "INCAR",
                        "action": {"_set": {"KSPACING": vi["INCAR"].get("KSPACING") * 0.8}},
                    }
                )
            else:
                actions.append({"dict": "INCAR", "action": {"_set": {"ISMEAR": 0, "SIGMA": 0.05}}})

        if "inv_rot_mat" in self.errors:
            actions.append({"dict": "INCAR", "action": {"_set": {"SYMPREC": 1e-8}}})

        if "brmix" in self.errors:
            # If there is not a valid OUTCAR already, increment
            # error count to 1 to skip first fix
            if self.error_count["brmix"] == 0:
                try:
                    assert Outcar(zpath(os.path.join(os.getcwd(), "OUTCAR"))).is_stopped is False
                except Exception:
                    self.error_count["brmix"] += 1

            if self.error_count["brmix"] == 0:
                # Valid OUTCAR - simply rerun the job and increment
                # error count for next time
                actions.append({"dict": "INCAR", "action": {"_set": {"ISTART": 1}}})
                self.error_count["brmix"] += 1

            elif self.error_count["brmix"] == 1:
                # Use Kerker mixing w/default values for other parameters
                actions.append({"dict": "INCAR", "action": {"_set": {"IMIX": 1}}})
                self.error_count["brmix"] += 1

            elif self.error_count["brmix"] == 2 and vi["KPOINTS"].style == Kpoints.supported_modes.Gamma:
                actions.append(
                    {
                        "dict": "KPOINTS",
                        "action": {"_set": {"generation_style": "Monkhorst"}},
                    }
                )
                actions.append({"dict": "INCAR", "action": {"_unset": {"IMIX": 1}}})
                self.error_count["brmix"] += 1

            elif self.error_count["brmix"] in [2, 3] and vi["KPOINTS"].style == Kpoints.supported_modes.Monkhorst:
                actions.append(
                    {
                        "dict": "KPOINTS",
                        "action": {"_set": {"generation_style": "Gamma"}},
                    }
                )
                actions.append({"dict": "INCAR", "action": {"_unset": {"IMIX": 1}}})
                self.error_count["brmix"] += 1

                if vi["KPOINTS"].num_kpts < 1:
                    all_kpts_even = all(bool(n % 2 == 0) for n in vi["KPOINTS"].kpts[0])
                    if all_kpts_even:
                        new_kpts = (tuple(n + 1 for n in vi["KPOINTS"].kpts[0]),)
                        actions.append(
                            {
                                "dict": "KPOINTS",
                                "action": {"_set": {"kpoints": new_kpts}},
                            }
                        )

            else:
                actions.append({"dict": "INCAR", "action": {"_set": {"ISYM": 0}}})
                if vi["KPOINTS"] is not None:
                    if vi["KPOINTS"].style == Kpoints.supported_modes.Monkhorst:
                        actions.append(
                            {
                                "dict": "KPOINTS",
                                "action": {"_set": {"generation_style": "Gamma"}},
                            }
                        )

                # Based on VASP forum's recommendation, you should delete the
                # CHGCAR and WAVECAR when dealing with this error.
                if vi["INCAR"].get("ICHARG", 0) < 10:
                    actions.append(
                        {
                            "file": "CHGCAR",
                            "action": {"_file_delete": {"mode": "actual"}},
                        }
                    )
                    actions.append(
                        {
                            "file": "WAVECAR",
                            "action": {"_file_delete": {"mode": "actual"}},
                        }
                    )

        if "zpotrf" in self.errors:
            # Usually caused by short bond distances. If on the first step,
            # volume needs to be increased. Otherwise, it was due to a step
            # being too big and POTIM should be decreased.  If a static run
            # try turning off symmetry.
            try:
                oszicar = Oszicar("OSZICAR")
                nsteps = len(oszicar.ionic_steps)
            except Exception:
                nsteps = 0

            if nsteps >= 1:
                potim = float(vi["INCAR"].get("POTIM", 0.5)) / 2.0
                actions.append({"dict": "INCAR", "action": {"_set": {"ISYM": 0, "POTIM": potim}}})
            elif vi["INCAR"].get("NSW", 0) == 0 or vi["INCAR"].get("ISIF", 0) in range(3):
                actions.append({"dict": "INCAR", "action": {"_set": {"ISYM": 0}}})
            else:
                s = vi["POSCAR"].structure
                s.apply_strain(0.2)
                actions.append({"dict": "POSCAR", "action": {"_set": {"structure": s.as_dict()}}})

            # Based on VASP forum's recommendation, you should delete the
            # CHGCAR and WAVECAR when dealing with this error.
            if vi["INCAR"].get("ICHARG", 0) < 10:
                actions.append({"file": "CHGCAR", "action": {"_file_delete": {"mode": "actual"}}})
                actions.append({"file": "WAVECAR", "action": {"_file_delete": {"mode": "actual"}}})

        if self.errors.intersection(["subspacematrix"]):
            if self.error_count["subspacematrix"] == 0:
                actions.append({"dict": "INCAR", "action": {"_set": {"LREAL": False}}})
            else:
                actions.append({"dict": "INCAR", "action": {"_set": {"PREC": "Accurate"}}})
            self.error_count["subspacematrix"] += 1

        if self.errors.intersection(["rspher", "real_optlay", "nicht_konv"]):
            s = vi["POSCAR"].structure
            if len(s) < self.natoms_large_cell:
                actions.append({"dict": "INCAR", "action": {"_set": {"LREAL": False}}})
            else:
                # for large supercell, try an in-between option LREAL = True
                # prior to LREAL = False
                if self.error_count["real_optlay"] == 0:
                    # use real space projectors generated by pot
                    actions.append({"dict": "INCAR", "action": {"_set": {"LREAL": True}}})
                elif self.error_count["real_optlay"] == 1:
                    actions.append({"dict": "INCAR", "action": {"_set": {"LREAL": False}}})
                self.error_count["real_optlay"] += 1

        if self.errors.intersection(["tetirr", "incorrect_shift"]):

            if vi["KPOINTS"] is not None:
                if vi["KPOINTS"].style == Kpoints.supported_modes.Monkhorst:
                    actions.append(
                        {
                            "dict": "KPOINTS",
                            "action": {"_set": {"generation_style": "Gamma"}},
                        }
                    )

        if "rot_matrix" in self.errors:
            if vi["KPOINTS"] is not None:
                if vi["KPOINTS"].style == Kpoints.supported_modes.Monkhorst:
                    actions.append(
                        {
                            "dict": "KPOINTS",
                            "action": {"_set": {"generation_style": "Gamma"}},
                        }
                    )
            else:
                actions.append({"dict": "INCAR", "action": {"_set": {"ISYM": 0}}})

        if "amin" in self.errors:
            actions.append({"dict": "INCAR", "action": {"_set": {"AMIN": "0.01"}}})

        if "triple_product" in self.errors:
            s = vi["POSCAR"].structure
            trans = SupercellTransformation(((1, 0, 0), (0, 0, 1), (0, 1, 0)))
            new_s = trans.apply_transformation(s)
            actions.append(
                {
                    "dict": "POSCAR",
                    "action": {"_set": {"structure": new_s.as_dict()}},
                    "transformation": trans.as_dict(),
                }
            )

        if "pricel" in self.errors:
            actions.append({"dict": "INCAR", "action": {"_set": {"SYMPREC": 1e-8, "ISYM": 0}}})

        if "brions" in self.errors:
            potim = float(vi["INCAR"].get("POTIM", 0.5)) + 0.1
            actions.append({"dict": "INCAR", "action": {"_set": {"POTIM": potim}}})

        if "zbrent" in self.errors:
            actions.append({"dict": "INCAR", "action": {"_set": {"IBRION": 1}}})
            actions.append({"file": "CONTCAR", "action": {"_file_copy": {"dest": "POSCAR"}}})

        if "too_few_bands" in self.errors:
            if "NBANDS" in vi["INCAR"]:
                nbands = int(vi["INCAR"]["NBANDS"])
            else:
                with open("OUTCAR") as f:
                    for line in f:
                        if "NBANDS" in line:
                            try:
                                d = line.split("=")
                                nbands = int(d[-1].strip())
                                break
                            except (IndexError, ValueError):
                                pass
            actions.append({"dict": "INCAR", "action": {"_set": {"NBANDS": int(1.1 * nbands)}}})

        if "pssyevx" in self.errors:
            actions.append({"dict": "INCAR", "action": {"_set": {"ALGO": "Normal"}}})
        if "eddrmm" in self.errors:
            # RMM algorithm is not stable for this calculation
            if vi["INCAR"].get("ALGO", "Normal") in ["Fast", "VeryFast"]:
                actions.append({"dict": "INCAR", "action": {"_set": {"ALGO": "Normal"}}})
            else:
                potim = float(vi["INCAR"].get("POTIM", 0.5)) / 2.0
                actions.append({"dict": "INCAR", "action": {"_set": {"POTIM": potim}}})
            if vi["INCAR"].get("ICHARG", 0) < 10:
                actions.append({"file": "CHGCAR", "action": {"_file_delete": {"mode": "actual"}}})
                actions.append({"file": "WAVECAR", "action": {"_file_delete": {"mode": "actual"}}})

        if "edddav" in self.errors:
            if vi["INCAR"].get("ICHARG", 0) < 10:
                actions.append({"file": "CHGCAR", "action": {"_file_delete": {"mode": "actual"}}})
            actions.append({"dict": "INCAR", "action": {"_set": {"ALGO": "All"}}})

        if "grad_not_orth" in self.errors:
            if vi["INCAR"].get("ISMEAR", 1) < 0:
                actions.append({"dict": "INCAR", "action": {"_set": {"ISMEAR": 0, "SIGMA": 0.05}}})

        if "zheev" in self.errors:
            if vi["INCAR"].get("ALGO", "Fast").lower() != "exact":
                actions.append({"dict": "INCAR", "action": {"_set": {"ALGO": "Exact"}}})
        if "elf_kpar" in self.errors:
            actions.append({"dict": "INCAR", "action": {"_set": {"KPAR": 1}}})

        if "rhosyg" in self.errors:
            if vi["INCAR"].get("SYMPREC", 1e-4) == 1e-4:
                actions.append({"dict": "INCAR", "action": {"_set": {"ISYM": 0}}})
            actions.append({"dict": "INCAR", "action": {"_set": {"SYMPREC": 1e-4}}})

        if "posmap" in self.errors:
            # VASP advises to decrease or increase SYMPREC by an order of magnitude
            # the default SYMPREC value is 1e-5
            if self.error_count["posmap"] == 0:
                # first, reduce by 10x
                orig_symprec = vi["INCAR"].get("SYMPREC", 1e-5)
                actions.append({"dict": "INCAR", "action": {"_set": {"SYMPREC": orig_symprec / 10}}})
            elif self.error_count["posmap"] == 1:
                # next, increase by 100x (10x the original)
                orig_symprec = vi["INCAR"].get("SYMPREC", 1e-6)
                actions.append({"dict": "INCAR", "action": {"_set": {"SYMPREC": orig_symprec * 100}}})
            else:
                # if we have already corrected twice, there's nothing else to do
                pass

        if "point_group" in self.errors:
            actions.append({"dict": "INCAR", "action": {"_set": {"ISYM": 0}}})

        if "symprec_noise" in self.errors:
            if (vi["INCAR"].get("ISYM", 2) > 0) and (vi["INCAR"].get("SYMPREC", 1e-5) > 1e-6):
                actions.append({"dict": "INCAR", "action": {"_set": {"SYMPREC": 1e-6}}})
            else:
                actions.append({"dict": "INCAR", "action": {"_set": {"ISYM": 0}}})

        VaspModder(vi=vi).apply_actions(actions)
        return {"errors": list(self.errors), "actions": actions}