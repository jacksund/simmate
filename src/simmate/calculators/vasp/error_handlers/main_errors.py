# -*- coding: utf-8 -*-

import os
import json
import shutil

from pymatgen.io.vasp.outputs import Outcar
from pymatgen.core.structure import Structure

from simmate.workflow_engine.error_handler import ErrorHandler
from simmate.calculators.vasp.inputs.incar import Incar
from simmate.calculators.vasp.outputs.oszicar import Oszicar

# !!! I really don't like how all of these errors are amassed into one class because
# it makes the logic difficult to follow and it raises questions about how to handle
# multiple errors showing up at once. I still convert this class from custodian,
# but in an admittedly lazy way (there aren't enough explanations for each correction).
# I'm going to revisit this and breakdown this class into smaller ones.


class MainVaspErrors(ErrorHandler):
    """
    A centralized class that handles a number of common errors that occur
    during VASP runs.
    """

    # run this while the VASP calculation is still going
    is_monitor = True

    # These are the error messages that we are looking for in the vasp.out file.
    # Note, that we can pick which ones we search for and which we ignore. See
    # the init for more on this.
    # Also note that some errors have multiple possible messages accossiated with
    # them (such as "tet").
    all_error_messages = {
        "tet": [
            "Tetrahedron method fails",
            "Fatal error detecting k-mesh",
            "Fatal error: unable to match k-point",
            "Routine TETIRR needs special values",
            "Tetrahedron method fails (number of k-points < 4)",
            "BZINTS",
        ],
        "inv_rot_mat": ["rotation matrix was not found (increase SYMPREC)"],
        "brmix": ["BRMIX: very serious problems"],
        "subspacematrix": ["WARNING: Sub-Space-Matrix is not hermitian in DAV"],
        "tetirr": ["Routine TETIRR needs special values"],
        "incorrect_shift": ["Could not get correct shifts"],
        "real_optlay": [
            "REAL_OPTLAY: internal error",
            "REAL_OPT: internal ERROR",
        ],
        "rspher": ["ERROR RSPHER"],
        "dentet": ["DENTET"],
        "too_few_bands": ["TOO FEW BANDS"],
        "triple_product": ["ERROR: the triple product of the basis vectors"],
        "rot_matrix": [
            "Found some non-integer element in rotation matrix",
            "SGRCON",
        ],
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
        "symprec_noise": [
            "determination of the symmetry of your systems shows a strong"
        ],
    }

    def __init__(
        self,
        natoms_large_cell=100,
        errors_to_catch=None,
        errors_to_ignore=None,
    ):

        # The threshold number of atoms to treat the cell as a large supercell.
        # This affects the handling of some errors.
        self.natoms_large_cell = natoms_large_cell

        # In some cases, we may not want to look for all the errors that this class
        # supports. In that case, we can give a list of the ones we want to look
        # for as well as a list of the ones we want to ignore.
        # If errors_to_catch is left as None, we look for all of them
        self.errors_to_catch = errors_to_catch or list(self.error_messages.keys())
        # Then remove any that were listed in errors_to_ignore
        for error in errors_to_ignore:
            self.errors_to_catch.pop(error)

    def check(self, dir):
        """
        Check for errors in the specified directory. Note, we assume that we are
        checking the vasp.out file. If that file is not present, we say that there
        is no error because another handler will address this.
        """

        # We want to return a list of errors that were found, so we keep a
        # master list.
        errors_found = []

        # establish the full path to the output file
        filename = os.path.join(dir, "vasp.out")

        # check to see that the file is there first
        if os.path.exists(filename):

            # read the file content and then close it
            with open(filename) as file:
                file_text = file.read()

            # Check if each error is present
            for error, message in self.error_messages.items():
                # if the error is NOT present, find() returns a -1
                if file_text.find(message) != -1:

                    # SPECIAL CASE: For brmix, we sometimes want to ignore this
                    if error == "brmix":
                        # load the INCAR file to view the current settings
                        incar_filename = os.path.join(dir, "INCAR")
                        incar = Incar.from_file(incar_filename)

                        # if NELECT is in the INCAR, that means we are running
                        # a charged calculation (e.g. defects). If this is the
                        # case, then we want to ingore a change in electron
                        # density (brmix) and move on to checking the next error.
                        if "NELECT" in incar:
                            continue

                    # add to our list of errors found
                    errors_found.append(error)

        # If the file doesn't exist, we are not seeing any error yetm which is
        # also an empty list. Otherwise return the list of errors we found
        return errors_found

    def correct(self, error, dir):
        """
        Perform corrections based on the INCAR and the list of errors returned by
        the check() method.

        Some errors have a series of fixes, where we want to keep a tally of
        how many times we tried fixing it. To keep track of these, a file named
        simmate_error_counts.json is written and updated.
        """

        # Note "error" here is a list of the errors found. For example, error
        # could be ["tet", "brmix", "rhosyg"]. If there weren't any errors found
        # then this is just and empty list.

        # Multiple corrections could be applied here so we record all of them.
        corrections = []

        # load the INCAR file to view the current settings
        incar_filename = os.path.join(dir, "INCAR")
        incar = Incar.from_file(incar_filename)

        # load the error-count file if it exists
        error_count_filename = os.path.join(dir, "simmate_error_counts.json")
        if os.path.exists(error_count_filename):
            with open(error_count_filename) as error_count_file:
                error_counts = json.load(error_count_file)
        # otherwise we are starting with an empty dictionary
        else:
            error_counts = {}

        # !!! why are these separate errors if they are always handled together?
        if "tet" in error and "dentet" in error:

            # check what the current KSPACING is. If it's not set, that means it's using
            # the default which is 0.5.
            current_kspacing = incar.get("KSPACING", 0.5)

            # If KSPACING isn't the default value, we try decreasing KSPACING
            # by 20% in each direction. which approximately doubles the number
            # of kpoints.
            if current_kspacing != 0.5:
                new_kspacing = current_kspacing * 0.8
                incar["KSPACING"] = new_kspacing
                corrections.appned(
                    f"switched KSPACING from {current_kspacing} to {new_kspacing}"
                )

            # otherwise we try changing the smearing method to guassian
            else:
                incar["ISMEAR"] = 0
                incar["SIGMA"] = 0.05
                corrections.append("switched ISMEAR to 0 and SIGMA to 0.05")

        if "inv_rot_mat" in error:
            incar["SYMPREC"] = 1e-8
            corrections.append("switched SYMPREC to 1e-8")

        if "brmix" in error:

            # The fix is based on the number of times we've already tried to
            # fix brmix. So let's make sure it's in our error_count dictionary.
            # If it isn't there yet, set the count to 0 and we'll update it below.
            error_counts["brmix"] = error_counts.get("brmix", 0)

            # The KGAMMA mode is relevent in a number of fixes below, so we
            # just grab that here. The default value is True.
            current_kgamma = incar.get("KGAMMA", True)

            # check if there is a valid OUTCAR
            if error_counts["brmix"] == 0:
                outcar_filename = os.path.join(dir, "OUTCAR")
                try:
                    assert Outcar(outcar_filename).is_stopped is False
                except Exception:
                    # if the OUTCAR isn't valid, we want to skip the first attempted
                    # correction below. We do this by adding 1 to our error count.
                    error_counts["brmix"] += 1

            if error_counts["brmix"] == 0:
                # If the OUTCAR is valid - simply rerun the job and increment
                # error count for next time.
                incar["ISTART"] = 1
                corrections.append("switched ISTART to 1")
                error_counts["brmix"] += 1

            elif error_counts["brmix"] == 1:
                # Use Kerker mixing w/default values for other parameters
                incar["IMIX"] = 1
                corrections.append("switched IMIX to 1")
                error_counts["brmix"] += 1

            elif error_counts["brmix"] == 2 and current_kgamma == True:
                # switch to Monkhorst and turn off Kerker mixing (IMIX=1)
                incar["KGAMMA"] = False
                corrections.append("switched KGAMMA to False")
                incar.pop("IMIX")
                corrections.append("removed any IMIX tag")
                error_counts["brmix"] += 1

            elif error_counts["brmix"] in [2, 3] and current_kgamma == False:
                # switch to Gamma and turn off Kerker mixing (IMIX=1)
                incar["KGAMMA"] = True
                corrections.append("switched KGAMMA to True")
                incar.pop("IMIX")
                corrections.append("removed any IMIX tag")
                error_counts["brmix"] += 1

                # TODO: I'm not sure what Custodian did here, so I haven't adapted
                # it yet. How can the number of kpoints be less than 1...?
                #
                # if vi["KPOINTS"].num_kpts < 1:
                #     all_kpts_even = all(bool(n % 2 == 0) for n in vi["KPOINTS"].kpts[0])
                #     if all_kpts_even:
                #         new_kpts = (tuple(n + 1 for n in vi["KPOINTS"].kpts[0]),)
                #         actions.append(
                #             {
                #                 "dict": "KPOINTS",
                #                 "action": {"_set": {"kpoints": new_kpts}},
                #             }
                #         )

            else:

                # Try turning off symmetry and using a Gamma-packed grid
                incar["ISYM"] = 0
                corrections.append("switched ISYM to 0")
                incar["KGAMMA"] = True
                corrections.append("switched KGAMMA to True")

                # Check the current ICHARG setting, where default is 0
                # If the ICHARG is less than 10, then we want to delete the CHGCAR
                # and WAVECAR to ensure the next run is a clean start.
                current_icharg = incar.get("ICHARG", 0)
                if current_icharg < 10:
                    os.remove(os.path.join(dir, "CHGCAR"))
                    os.remove(os.path.join(dir, "WAVECAR"))
                corrections.append("deleted CHGCAR and WAVECAR")

                # BUG: why doesn't custodian add an attempt here?
                # error_counts["brmix"] += 1

        if "zpotrf" in error:

            # We can learn more about the cause of this error by looking at
            # the OSZICAR and checking the number of steps completed.
            # BUG: what if the OSCZICAR is improperly formatted but a number
            # of ionic steps completed successfully?
            try:
                oszicar_filename = os.path.join(dir, "OSZICAR")
                oszicar = Oszicar(oszicar_filename)
                nionic_steps = len(oszicar.ionic_steps)
            except Exception:
                nionic_steps = 0

            # If the error shows up after the first ionic step, then this is likely
            # caused by POTIM being too large.
            if nionic_steps >= 1:
                # Halve the POTIM and turn off symmetry
                current_potim = incar.get("POTIM", 0.5)
                new_potim = current_potim / 2
                incar["POTIM"] = new_potim
                corrections.append(f"switch POTIM from {current_potim} to {new_potim}")
                incar["ISYM"] = 0
                corrections.append("set ISYM to 0")

            # If this is a static calculation (NSW=0) or if ISIF is 1-3, then
            # we just want to turn off symmetry
            elif incar.get("NSW", 0) == 0 or incar.get("ISIF", 0) in [0, 1, 3]:
                incar["ISYM"] = 0
                corrections.append("set ISYM to 0")

            # If the error shows up on the first ionic step, it is likely that
            # our bond distances are too small. A simple fix is to scale our
            # starting lattice. We also save the original structure to a file
            # name POSCAR_original in case it's needed elsewhere.
            else:
                poscar_filename = os.path.join(dir, "POSCAR")
                structure = Structure.from_file(poscar_filename)
                structure.to("POSCAR", poscar_filename + "_original")
                structure.apply_strain(0.2)
                structure.to("POSCAR", poscar_filename)
                corrections.append("scaled the structure lattice by +20%")

            # Check the current ICHARG setting, where default is 0
            # If the ICHARG is less than 10, then we want to delete the CHGCAR
            # and WAVECAR to ensure the next run is a clean start.
            current_icharg = incar.get("ICHARG", 0)
            if current_icharg < 10:
                os.remove(os.path.join(dir, "CHGCAR"))
                os.remove(os.path.join(dir, "WAVECAR"))
            corrections.append("deleted CHGCAR and WAVECAR")

        if "subspacematrix" in error:

            # The fix is based on the number of times we've already tried to
            # fix this. So let's make sure it's in our error_count dictionary.
            # If it isn't there yet, set the count to 0.
            # Also increase the count by 1, as this is our new addition
            error_counts["subspacematrix"] = error_counts.get("subspacematrix", 0) + 1

            # On our first try, change evalutating projection operators
            # in reciprocal space.
            if error_counts["subspacematrix"] == 0:
                incar["LREAL"] = False
                corrections.append("set LREAL to False")
            # As a last resort, try changing the precision
            else:
                incar["PREC"] = "Accurate"
                corrections.append("set PREC to Accurate")

        if error.intersection(["rspher", "real_optlay", "nicht_konv"]):

            # The fix is based on the number of times we've already tried to
            # fix brmix. So let's make sure it's in our error_count dictionary.
            # If it isn't there yet, set the count to 0 and we'll update it below.
            error_counts["real_optlay"] = error_counts.get("real_optlay", 0)

            poscar_filename = os.path.join(dir, "POSCAR")
            structure = Structure.from_file(poscar_filename)

            if structure.num_sites < self.natoms_large_cell:
                incar["LREAL"] = False
                corrections.append("set LREAL to False")

            else:
                # for large supercell, try an in-between option LREAL = True
                # prior to LREAL = False
                if error_counts["real_optlay"] == 0:
                    # use real space projectors generated by pot
                    incar["LREAL"] = True
                    corrections.append("set LREAL to True")
                elif error_counts["real_optlay"] == 1:
                    incar["LREAL"] = False
                    corrections.append("set LREAL to False")
                error_counts["real_optlay"] += 1

        if error.intersection(["tetirr", "incorrect_shift"]):
            incar["KGAMMA"] = True
            corrections.append("switched KGAMMA to True")

        if "rot_matrix" in error:
            incar["KGAMMA"] = True
            corrections.append("switched KGAMMA to True")
            # TODO: 2nd attempt is to turn ISYM=0

        if "amin" in self.errors:
            incar["AMIN"] = 0.01
            corrections.append("switched AMIN to 0.01")

        if "triple_product" in self.errors:
            poscar_filename = os.path.join(dir, "POSCAR")
            structure = Structure.from_file(poscar_filename)
            structure.to("POSCAR", poscar_filename + "_original")
            structure.make_supercell([[1, 0, 0], [0, 0, 1], [0, 1, 0]])
            structure.to("POSCAR", poscar_filename)
            corrections.append("adjusted lattice basis to swap b and c vectors")

        if "pricel" in error:
            incar["SYMPREC"] = 1e-8
            corrections.append("switched SYMPREC to 1e-8")
            incar["ISYM"] = 0
            corrections.append("switched ISYM to 0")

        if "brions" in error:
            current_potim = incar.get("POTIM", 0.5)
            new_potim = current_potim + 0.1
            incar["POTIM"] = new_potim
            corrections.append("switched POTIM from {current_potim} to {new_potim}")

        if "zbrent" in error:
            incar["IBRION"] = 1
            corrections.append("switched IBRION to 1")
            poscar_filename = os.path.join(dir, "POSCAR")
            contcar_filename = os.path.join(dir, "CONTCAR")
            shutil.copyfile(contcar_filename, poscar_filename)
            corrections.append("copied the CONTCAR over to the POSCAR")

        if "too_few_bands" in self.errors:
            # Grab the current number of bands. First check the INCAR and if
            # it isn't there, jump to the OUTCAR.
            if "NBANDS" in incar:
                nbands_current = incar["NBANDS"]
            else:
                outcar_filename = os.path.join(dir, "OUTCAR")
                with open(outcar_filename) as file:
                    lines = file.readlines()
                # Go through the lines until we find the NBANDS one. The value
                # should be at the very end of the line.
                for line in lines:
                    if "NBANDS" in line:
                        nbands_current = int(line.split()[-1])
                        break
            # increase the number of bands by 10%
            nbands_new = nbands_current * 1.1
            incar["NBANDS"] = nbands_new
            corrections.append(
                f"switch NBANDS from {nbands_current} to {nbands_new} (+10%)"
            )

        if "pssyevx" in error:
            incar["ALGO"] = "Normal"
            corrections.append("switched ALGO to Normal")

        if "eddrmm" in error:
            # RMM algorithm is not stable for this calculation
            if incar.get("ALGO", "Normal") in ["Fast", "VeryFast"]:
                incar["ALGO"] = "Normal"
                corrections.append("switched ALGO to Normal")
            else:
                # Halve the POTIM
                current_potim = incar.get("POTIM", 0.5)
                new_potim = current_potim / 2
                incar["POTIM"] = new_potim
                corrections.append(f"switch POTIM from {current_potim} to {new_potim}")

            # Check the current ICHARG setting, where default is 0
            # If the ICHARG is less than 10, then we want to delete the CHGCAR
            # and WAVECAR to ensure the next run is a clean start.
            current_icharg = incar.get("ICHARG", 0)
            if current_icharg < 10:
                os.remove(os.path.join(dir, "CHGCAR"))
                os.remove(os.path.join(dir, "WAVECAR"))
            corrections.append("deleted CHGCAR and WAVECAR")

        if "edddav" in error:
            current_icharg = incar.get("ICHARG", 0)
            if current_icharg < 10:
                os.remove(os.path.join(dir, "CHGCAR"))
                corrections.append("deleted CHGCAR")
            incar["ALGO"] = "All"
            corrections.append("switched ALGO to Normal")

        if "grad_not_orth" in error:
            if incar.get("ISMEAR", 1) < 0:
                incar["ISMEAR"] = "0"
                corrections.append("switched ALGO to Normal")
                incar["SIGMA"] = 0.05
                corrections.append("switched SIGMA to 0.05")

        if "zheev" in error:
            if incar.get("ALGO", "Fast") != "Exact":
                incar["ALGO"] = "Exact"
                corrections.append("switched Algo to Exact")

        if "elf_kpar" in error:
            incar["KPAR"] = 1
            corrections.append("switched KPAR to 1")

        if "rhosyg" in error:
            if incar.get("SYMPREC", 1e-4) == 1e-4:
                incar["ISYM"] = 0
                corrections.append("switched KPAR to 1")
            incar["SYMPREC"] = 1e-4
            corrections.append("switched SYMPREC to 1e-4")

        if "posmap" in error:
            # VASP advises to decrease or increase SYMPREC by an order of magnitude
            # the default SYMPREC value is 1e-5

            error_counts["posmap"] = error_counts.get("posmap", 0) + 1

            if error_counts["posmap"] == 0:
                # first, reduce by 10x
                current_symprec = incar.get("SYMPREC", 1e-5)
                new_symprec = current_symprec / 10
                incar["SYMPREC"] = new_symprec
                corrections.append(
                    f"switched SYMPREC from {current_symprec} to {new_symprec}"
                )

            elif error_counts["posmap"] == 1:
                # next, increase by 100x (10x the original because we descreased
                # by 10x in the first try.)
                current_symprec = incar.get("SYMPREC", 1e-5)
                new_symprec = current_symprec * 100
                incar["SYMPREC"] = new_symprec
                corrections.append(
                    f"switched SYMPREC from {current_symprec} to {new_symprec}"
                )

        if "point_group" in error:
            incar["ISYM"] = 0
            corrections.append("switched ISYM to 0")

        if "symprec_noise" in error:
            if incar.get("ISYM", 2) > 0 and incar.get("SYMPREC", 1e-5) > 1e-6:
                incar["SYMPREC"] = 1e-6
                corrections.append("switched SYMPREC to 1e-6")
            else:
                incar["ISYM"] = 0
                corrections.append("switched ISYM to 0")

        # Now that we made all of our changes to the INCAR, we can rewrite it
        incar.to_file(incar_filename)

        #!!! BUG: rewrite simmate_error_counts!

        # return the list of corrections we made
        return corrections
