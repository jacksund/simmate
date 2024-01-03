# -*- coding: utf-8 -*-

# Alternative implementations of this class from ASE and PyMatGen
# https://gitlab.com/ase/ase/-/blob/master/ase/io/espresso.py
# https://github.com/materialsproject/pymatgen/blob/master/pymatgen/io/pwscf.py

import logging
from pathlib import Path

from pymatgen.core import Lattice

from simmate.apps.quantum_espresso.inputs.k_points import Kpoints
from simmate.apps.quantum_espresso.inputs.pwscf_in_modifiers import (
    keyword_modifier_ecutrho,
    keyword_modifier_ecutwfc,
    keyword_modifier_nat,
    keyword_modifier_ntyp,
    keyword_modifier_pseudo_dir,
)
from simmate.toolkit import Structure
from simmate.utilities import str_to_datatype


class PwscfInput:
    """
    Base input file class. Right now, it does not support symmetry and is
    very basic.

    The official input file docs (which this class wraps) is located here:
        https://www.quantum-espresso.org/Doc/INPUT_PW.html

    Currently we make the following assumptions about the file:
        - section titles are in all caps
        - all key-value pairs are on separate lines
        - there are no commas at the end of lines (for key-value pair sections)
        - float values use "e" instead of "d" (ex: 1.23e-4)
        - no "if_pos" values are used in the ATOMIC_POSITIONS section
        - use CELL_PARAMETERS with 'angstrom'. avoid `alat` and `bohr`
        - use ATOMIC_POSITIONS with 'crystal' or 'angstrom'. avoid others
    """

    # This class is a fork of PWInput from pymatgen. Many changes have been
    # made, but it good to know where we start & where we can contrib back to.
    # https://github.com/materialsproject/pymatgen/blob/master/pymatgen/io/pwscf.py

    PARAMETER_SECTIONS = [
        # key-value pairs
        "&CONTROL",
        "&SYSTEM",
        "&ELECTRONS",
        "&IONS",
        "&CELL",
        "&FCP",
        "&RISM",
        # structure-based (each has a unique format)
        "ATOMIC_SPECIES",
        "ATOMIC_POSITIONS",
        "K_POINTS",
        "ADDITIONAL_K_POINTS",
        "CELL_PARAMETERS",
        "CONSTRAINTS",
        "OCCUPATIONS",
        "ATOMIC_VELOCITIES",
        "ATOMIC_FORCES",
        "SOLVENTS",
        "HUBBARD",
    ]

    # establish type mappings for common parameters.
    # Note: this is for ALL sections (control, system, electrons, etc.)
    PARAMETER_MAPPINGS = {
        # STRINGS - these must be quoted in the input file
        "calculation": str,
        "title": str,
        "verbosity": str,
        "restart_mode": str,
        "outdir": str,
        "wfcdir": str,
        "prefix": str,
        "disk_io": str,
        "pseudo_dir": str,
        "occupations": str,
        "smearing": str,
        "pol_type": str,
        "input_dft": str,
        "exxdiv_treatment": str,
        "dmft_prefix": str,
        "constrained_magnetization": str,
        "assume_isolated": str,
        "esm_bc": str,
        "vdw_corr": str,
        "mixing_mode": str,
        "diagonalization": str,
        "efield_phase": str,
        "startingpot": str,
        "startingwfc": str,
        "ion_positions": str,
        "ion_velocities": str,
        "ion_dynamics": str,
        "pot_extrapolation": str,
        "wfc_extrapolation": str,
        "ion_temperature": str,
        "cell_dynamics": str,
        "cell_dofree": str,
        "fcp_dynamics": str,
        "fcp_temperature": str,
        "closure": str,
        "starting1d": str,
        "starting3d": str,
        "laue_wall": str,
        # BOOLEANS
        "wf_collect": bool,
        "tstress": bool,
        "tprnfor": bool,
        "lkpoint_dir": bool,
        "tefield": bool,
        "dipfield": bool,
        "lelfield": bool,
        "lorbm": bool,
        "lberry": bool,
        "lfcpopt": bool,
        "monopole": bool,
        "nosym": bool,
        "nosym_evc": bool,
        "noinv": bool,
        "no_t_rev": bool,
        "force_symmorphic": bool,
        "use_all_frac": bool,
        "one_atom_occupations": bool,
        "starting_spin_angle": bool,
        "noncolin": bool,
        "x_gamma_extrapolation": bool,
        "lda_plus_u": bool,
        "lspinorb": bool,
        "london": bool,
        "ts_vdw_isolated": bool,
        "xdm": bool,
        "uniqueb": bool,
        "rhombohedral": bool,
        "realxz": bool,
        "block": bool,
        "scf_must_converge": bool,
        "adaptive_thr": bool,
        "diago_full_acc": bool,
        "tqr": bool,
        "remove_rigid_rot": bool,
        "refold_pos": bool,
        # FLOATS
        "etot_conv_thr": float,
        "forc_conv_thr": float,
        "conv_thr": float,
        "Hubbard_U": float,
        "Hubbard_J0": float,
        "degauss": float,
        "starting_magnetization": float,
        # INTEGERS
        "nstep": int,
        "iprint": int,
        "nberrycyc": int,
        "gdir": int,
        "nppstr": int,
        "ibrav": int,
        "nat": int,
        "ntyp": int,
        "nbnd": int,
        "nr1": int,
        "nr2": int,
        "nr3": int,
        "nr1s": int,
        "nr2s": int,
        "nr3s": int,
        "nspin": int,
        "nqx1": int,
        "nqx2": int,
        "nqx3": int,
        "lda_plus_u_kind": int,
        "edir": int,
        "report": int,
        "esm_nfit": int,
        "space_group": int,
        "origin_choice": int,
        "electron_maxstep": int,
        "mixing_ndim": int,
        "mixing_fixed_ns": int,
        "ortho_para": int,
        "diago_cg_maxiter": int,
        "diago_david_ndim": int,
        "nraise": int,
        "bfgs_ndim": int,
        "if_pos": int,
        "nks": int,
        "nk1": int,
        "nk2": int,
        "nk3": int,
        "sk1": int,
        "sk2": int,
        "sk3": int,
        "nconstr": int,
    }

    def __init__(
        self,
        structure: Structure,
        kpoints: Kpoints,
        psuedo_mappings: dict = {},
        control: dict = {},
        system: dict = {},
        electrons: dict = {},
        ions: dict = {},
        cell: dict = {},
        fcp: dict = {},
        rism: dict = {},
    ):
        """
        Initializes a PWSCF input file.
        """

        # check for psuedo mappings:
        if not psuedo_mappings:
            logging.warning(
                "No psuedopotential mappings were provided. If you are trying to "
                "use the Simmate defaults (from SSSP), then make sure you have "
                "ran 'simmate-qe setup sssp' to download the files for you. "
                "Otherwise, make sure you provide a mapping and that the "
                "files are present in '~/simmate/quantum_espresso/potentials'"
            )

        self.structure = structure
        self.kpoints = kpoints
        self.psuedo_mappings = psuedo_mappings

        self.control = control
        self.system = system
        self.electrons = electrons
        self.ions = ions
        self.cell = cell
        self.fcp = fcp
        self.rism = rism

    # -------------------------------------------------------------------------

    # Loading methods

    @classmethod
    def from_file(cls, filename: Path | str = "INCAR"):
        """
        Builds an PwscfInput object from a file.
        """
        filename = Path(filename)
        with filename.open() as file:
            content = file.read()
        return cls.from_str(content)

    @classmethod
    def from_str(cls, content: str):
        """
        Builds an PwscfInput object from a string.
        """
        # split the file content into separate lines
        lines = content.split("\n")

        # organize all lines by their section headers
        sections = {}
        current_section = None
        for line in lines:
            # clean the line
            line = line.strip()

            # If the line starts with a # or ! then its a comment and we should skip.
            # It also could be an empty line that we should skip,
            if (
                # empty lines
                not line
                or line.startswith("\n")
                # comment lines
                or line.startswith("#")
                or line.startswith("!")
                # end of section
                or line == "/"
            ):
                continue
            # Check to see if the line is the start of a new section
            # Note, we only grab the first 'word' because you can have headers
            # such as "ATOMIC_POSITIONS angstrom" or "ATOMIC_POSITIONS alat"
            elif line.strip().split()[0] in cls.PARAMETER_SECTIONS:
                current_section = line
                sections[current_section] = []
            else:
                assert current_section is not None  # bug-check
                sections[current_section].append(line)

        # now go through each section and convert/format to as needed
        sections_cleaned = {}
        for section, lines in sections.items():
            # ----------------------

            # these sections are key-value pairs and give a dictionary
            if section in [
                "&CONTROL",
                "&SYSTEM",
                "&ELECTRONS",
                "&IONS",
                "&CELL",
                "&FCP",
                "&RISM",
            ]:
                section_name = section.replace("&", "").lower()
                section_data = {}
                for line in lines:
                    parameter, value = [i.strip() for i in line.split("=")]
                    section_data[parameter] = str_to_datatype(
                        parameter=parameter,
                        value=value,
                        type_mappings=cls.PARAMETER_MAPPINGS,
                        strip_quotes=True,
                    )

            # All other sections need special handling
            # ----------------------

            elif section == "ATOMIC_SPECIES":
                section_name = section.lower()
                section_data = []
                # each line follows...
                #   X(symbol)    Mass_X     PseudoPot_X
                # for ex:
                #   Si  28.086  Si.pz-vbc.UPF
                # Note: mass is only used for MD calcs.
                for line in lines:
                    element, mass, psuedo_file = line.strip().split()
                    # TODO: use an Element base class...?
                    specie = {
                        "element": element.strip(),
                        "mass": mass.strip(),
                        "psuedo_file": psuedo_file.strip(),
                    }
                    section_data.append(specie)

            # ----------------------

            elif section.startswith("ATOMIC_POSITIONS"):
                section_name, section_mode = section.lower().split()
                section_data = {
                    "mode": section_mode,
                    "data": [],
                }
                # each line follows...
                #   X(symbol)    x    y    z
                # for ex:
                #   Si 0.00 0.00 0.00
                #   Si 0.25 0.25 0.25
                # Note: mass is only used for MD calcs.
                for line in lines:
                    # TODO: use a PeriodicSite base class...?
                    element, x, y, z = line.strip().split()
                    specie = {
                        "element": element.strip(),
                        "coords": [float(x), float(y), float(z)],
                    }
                    section_data["data"].append(specie)

            # ----------------------

            elif section.startswith("K_POINTS") or section.startswith(
                "ADDITIONAL_K_POINTS"
            ):
                section_name, *section_mode = section.lower().split()
                if not section_mode:
                    section_mode = "tpiba"  # using default value
                    # Note: if the is NO section at all, then the default is
                    # actually gamma. This is handled within `from_dict`
                else:
                    section_mode = section_mode[0]
                section_data = {
                    "mode": section_mode,
                    "data": [],
                }
                if section_mode == "gamma":
                    section_data.pop("data")  # no extra info needed
                elif section_mode == "automatic":
                    # there should be a single line for this mode.
                    #   nk1  nk2  nk3  sk1  sk2  sk3
                    # n = grid, s = offset
                    assert len(lines) == 1
                    nk1, nk2, nk3, sk1, sk2, sk3 = lines[0].strip().split()
                    section_data["data"] = {
                        "grid": [int(nk1), int(nk2), int(nk3)],
                        "offset": [int(sk1), int(sk2), int(sk3)],
                    }

                elif section_mode in [
                    "tpiba",
                    "crystal",
                    "tpiba_b",
                    "crystal_b",
                    "tpiba_c",
                    "crystal_c",
                ]:
                    # The first line is always just the total number of kpts.
                    # nkpts = line[0]  # we don't store this because it can be inferred

                    # Then each line follows...
                    #   xk_x(1) 	 xk_y(1) 	 xk_z(1) 	 wk(1)
                    # for ex:
                    #   10
                    #   0.1250000  0.1250000  0.1250000   1.00
                    #   0.1250000  0.1250000  0.3750000   3.00
                    #   ..... (+ 8 more lines for kpts)
                    for line in lines[1:]:
                        x, y, z, weight = line.strip().split()
                        kpt = {
                            "coords": [float(x), float(y), float(z)],
                            "weight": float(weight),
                        }
                        section_data["data"].append(kpt)

            # ----------------------

            elif section.startswith("CELL_PARAMETERS"):
                section_name, section_mode = section.lower().split()
                section_data = {
                    "mode": section_mode,
                    "data": [],
                }
                # section format follows...
                #   v1(1)  v1(2)  v1(3)    ... 1st lattice vector
                #   v2(1)  v2(2)  v2(3)    ... 2nd lattice vector
                #   v3(1)  v3(2)  v3(3)    ... 3rd lattice vector
                assert len(lines) == 3  # bug-check
                lattice = [[float(v.strip()) for v in l.split()] for l in lines]
                section_data["data"].append(lattice)

            # ----------------------

            elif section == "CONSTRAINTS":
                raise NotImplementedError()  # TODO

            elif section == "OCCUPATIONS":
                raise NotImplementedError()  # TODO

            elif section.startswith("ATOMIC_VELOCITIES"):
                raise NotImplementedError()  # TODO

            elif section == "ATOMIC_FORCES":
                raise NotImplementedError()  # TODO

            elif section.startswith("SOLVENTS"):
                raise NotImplementedError()  # TODO

            elif section.startswith("HUBBARD"):
                raise NotImplementedError()  # TODO

            # ----------------------

            # regardless of the method above, we now have cleaned the section
            sections_cleaned[section_name] = section_data

        # we now have all the infomation we need in a clean dictionary format
        return cls.from_dict(sections_cleaned)

    @classmethod
    def from_dict(cls, data: dict):
        # We do not yet support symmetry-based inputs for lattice/structures
        lattice_symmetry = data["system"]["ibrav"]  # ibrav is a required input
        if lattice_symmetry != 0:
            raise NotImplementedError("PwscfInput currently only supports ibrav=0")
            # TODO: add support via Structure.from_spacegroup

        # ----------------------

        # build the lattice

        lattice_parameters = data.get("cell_parameters")
        if not lattice_parameters:
            raise Exception(
                "PwscfInput requires cell parameters to determine the structure"
            )

        # regardless of input, we convert to Angstrom for simmate
        lattice_units = lattice_parameters.get("mode")
        if lattice_units == "alat":
            raise NotImplementedError("alat is not yet supported for cell parameters")
        elif lattice_units == "bohr":
            raise NotImplementedError("bohr is not yet supported for cell parameters")
        elif lattice_units == "angstrom":
            # we already have the matrix in proper units
            lattice_matrix = lattice_parameters["data"]
        else:
            raise Exception(f"Unknown cell parameters mode: {lattice_units}.")

        lattice = Lattice(matrix=lattice_matrix)

        # ----------------------

        # build the structure using lattice + atomic sites

        site_parameters = data.get("atomic_positions")
        if not site_parameters:
            raise Exception(
                "PwscfInput requires atomic positions to determine the structure"
            )

        # regardless of input, we convert to either Angstrom or fractional coords
        site_units = site_parameters.get("mode")
        if site_units == "alat":
            raise NotImplementedError("alat is not yet supported for cell parameters.")
        elif site_units == "bohr":
            raise NotImplementedError("bohr is not yet supported for cell parameters.")
        elif site_units == "angstrom":
            coords_are_cartesian = True
            lattice_matrix = lattice_parameters["data"]
        elif site_units == "crystal":
            coords_are_cartesian = False
        elif site_units == "crystal_sg":
            raise NotImplementedError(
                "crystal_sg is not yet supported for cell parameters."
            )
        else:
            raise Exception(f"Unknown atomic positions mode: {lattice_units}.")

        # regardless of mode, we bring all site coords and elements into
        # independent lists
        species = [site["element"] for site in site_parameters["data"]]
        coords = [site["coords"] for site in site_parameters["data"]]

        structure = Structure(
            lattice=lattice,
            species=species,
            coords=coords,
            coords_are_cartesian=coords_are_cartesian,
        )

        # ----------------------

        # build k-points info
        # TODO: have base class to help here + merge with VASP

        kpt_parameters = data.get("k_points", {})
        # default when no section at all is a single point gamma kpt
        kpoints_mode = kpt_parameters.get("mode", "gamma")

        if kpoints_mode == "gamma":  # Use only the Gamma point.
            kpoints_grid = None
            kpoints_offset = None
            kpoints_weights = None
        elif (
            kpoints_mode == "automatic"
        ):  # Automatically generate a Monkhorst-Pack grid
            kpoints_grid = kpt_parameters["data"]["grid"]
            kpoints_offset = kpt_parameters["data"]["offset"]
            kpoints_weights = None
        elif kpoints_mode in [
            "tpiba",  # Monkhorst-Pack grid specified in reciprocal lattice units
            "crystal",  # Specify k-points in crystal coordinates.
        ]:
            kpoints_offset = None
            kpoints_grid = [k["coords"] for k in kpt_parameters["data"]]
            kpoints_weights = [k["weight"] for k in kpt_parameters["data"]]
        elif kpoints_mode in [
            "tpiba_b",  # Monkhorst-Pack grid specified in reciprocal lattice units, with a shift.
            "tpiba_c",  #  Monkhorst-Pack grid specified in reciprocal lattice units, with a different shift.
            "crystal_b",  # Specify k-points in crystal coordinates with a shift.
            "crystal_c",  # Specify k-points in crystal coordinates with a different shift.
        ]:
            raise NotImplementedError(
                f"{kpoints_mode} is not yet supported for k points"
            )
        else:
            raise Exception(f"Unknown k points mode: {kpoints_mode}.")

        kpoints = Kpoints(
            mode=kpoints_mode,
            grid=kpoints_grid,
            offset=kpoints_offset,
            weights=kpoints_weights,
        )

        # ----------------------

        return cls(
            structure=structure,
            kpoints=kpoints,
            control=data.get("control", {}),  # !!! should I pop psuedo_file?
            system=data.get("system", {}),
            electrons=data.get("electrons", {}),
            ions=data.get("ions", {}),
            cell=data.get("cell", {}),
            fcp=data.get("fcp", {}),
            rism=data.get("rism", {}),
        )

    # -------------------------------------------------------------------------

    # Export methods

    def to_str(self) -> str:
        final_str = ""

        # ----------------------

        # place key-value sections up top
        # Note: we pull the final evaluated settings, which fills out modifiers
        # such as "__per_atom" or "__auto__"

        for section, content in self.evaluated_settings.items():
            if not content:
                continue

            # section title
            final_str += f"&{section.upper()}\n"
            # parameters (we copy because we modify values some)
            for key, value in content.copy().items():
                # if the input type is a str, we want to make sure it's
                # wrapped in single quotes for pw-scf to read
                if self.PARAMETER_MAPPINGS.get(key) == str:
                    value = f"'{value}'"
                # booleans are written differently than in python
                elif self.PARAMETER_MAPPINGS.get(key) == bool:
                    value = f".{str(value).lower()}."
                final_str += f"\t{key} = {value}\n"
            # section ending
            final_str += "/\n\n"

        # ----------------------

        # then write structural information

        # lattice info
        # string is the same as str(lattice) but we just indent the entire thing
        final_str += "CELL_PARAMETERS angstrom\n"
        lattice_str = str(self.structure.lattice).replace("\n", "\n ")
        final_str += f" {lattice_str}\n\n"

        # specie info
        final_str += "ATOMIC_SPECIES\n"
        for element in self.structure.composition:
            psuedo_name = self.psuedo_mappings[element.symbol]["filename"]
            final_str += (
                f" {element.symbol}  {float(element.atomic_mass)}  {psuedo_name}\n"
            )
        final_str += "\n"  # extra empty line after final specie

        # site info
        # ATOMIC_POSITIONS (angstrom or crystal)
        site_mode = "crystal"  # !!! we assume frac coords for now
        final_str += f"ATOMIC_POSITIONS {site_mode}\n"
        for site in self.structure:
            final_str += f" {site.specie.symbol} {site.a} {site.b} {site.c}\n"
        final_str += "\n"  # extra empty line after final site

        # ----------------------

        # then write kpoint information

        # we evaluate the class in case there are modifiers like __kpt_density
        kpoints = self.evaluated_k_points

        final_str += f"K_POINTS {kpoints.mode}\n"
        if kpoints.mode == "gamma":
            pass  # no extra lines needed

        elif kpoints.mode == "automatic":
            # a single line is needed
            nk1, nk2, nk3 = kpoints.grid
            sk1, sk2, sk3 = kpoints.offset
            final_str += f" {nk1} {nk2} {nk3} {sk1} {sk2} {sk3}\n"

        elif kpoints.mode in ["tpiba", "crystal"]:
            final_str += f" {len(self.kpoints.grid)}\n"
            for kpt, kpt_wt in zip(kpoints.grid, kpoints.weights):
                final_str += f" {kpt[0]} {kpt[1]} {kpt[2]} {kpt_wt}\n"

        elif kpoints.mode in [
            "tpiba_b",
            "tpiba_c",
            "crystal_b",
            "crystal_c",
        ]:
            raise NotImplementedError(
                f"{kpoints.mode} is not yet supported for k points"
            )

        else:
            raise Exception(f"Unknown k points mode: {kpoints.mode}.")

        final_str += "\n"

        # ----------------------

        return final_str

    def to_file(self, filename: Path | str = "pwscf.in"):
        """
        Write PWSCF input settings to a file.
        Args:
            filename (str): filename to write to.
        """
        # we just take the string format and put it in a file
        filename = Path(filename)
        with filename.open("w") as file:
            file.write(self.to_str())

    # -------------------------------------------------------------------------

    @property
    def evaluated_settings(self) -> dict:
        final_settings = {}

        for section in [
            "control",
            "system",
            "electrons",
            "ions",
            "cell",
            "fcp",
            "rism",
        ]:
            content = getattr(self, section)
            if content:
                final_settings[section] = self._evaluate_dict(content)

        return final_settings

    def _evaluate_dict(self, data: dict) -> dict:
        # TODO: Refactor and combine this functionality with vasp.Incar

        # First we need to iterate through all parameters and check if we have
        # ones that are structure-specific. For example, we would need to
        # evaluate "ecutwfc__per_atom". We go through all these and collect the
        # parameters into a final settings list.
        final_settings = {}
        for parameter, value in data.items():
            # if there is no modifier attached to the parameter, we just keep it as-is
            if "__" not in parameter:
                final_settings[parameter] = value

            # Otherwise we have a modifier like "__density" and need to evaluate it
            else:
                # make sure we have a structure supplied because all modifiers
                # require one.
                if not self.structure:
                    raise Exception(
                        "It looks like you used a keyword modifier but didn't "
                        f"supply a structure! If you want to use {parameter}, "
                        "then you need to make sure you provide a structure so "
                        "that the modifier can be evaluated."
                    )

                # separate the input into the base parameter and modifier.
                # This also overwrites what our paramter value is.
                parameter, modifier_tag = parameter.split("__")

                # check that this class has this modifier supported. It should
                # be a method named "keyword_modifier_mymodifier".
                # If everything looks good, we grab the modifier function.
                # If the tag is just "auto", then we look for a tag that is
                # named after the input variable
                if modifier_tag == "auto":
                    modifier_fxn_name = "keyword_modifier_" + parameter
                else:
                    modifier_fxn_name = "keyword_modifier_" + modifier_tag
                if hasattr(self, modifier_fxn_name):
                    modifier_fxn = getattr(self, modifier_fxn_name)
                else:
                    raise AttributeError(
                        """
                        It looks like you used a keyword modifier that hasn't
                        been defined yet! If you want something like `ENCUT__per_atom`,
                        then you need to make sure there is a `keyword_modifier_per_atom`
                        method available. "auto" modifiers are a special case where,
                        `ENCUT__auto` needs the method to be `keyword_modifier_ENCUT`.
                        """
                    )

                # now that we have the modifier function, let's use it to update
                # our value for this keyword.
                value = modifier_fxn(self.structure, value)

                # sometimes the modifier returns None. In this case we don't
                # set anything in the INCAR, but leave it to the programs
                # default value.
                if not value:
                    continue
                # BUG: Are there cases where None is return but we still want
                # to write it to the INCAR? If so, it'd be skipped here.

                # if the "parameter" is actually "multiple_keywords", then we
                # have our actual parameters as a dictionary. We need to
                # pull these out of the "value" we have.
                if parameter == "multiple_keywords":
                    for subparameter, subvalue in value.items():
                        final_settings[subparameter] = subvalue

                # otherwise we were just given back an update value
                else:
                    final_settings[parameter] = value
        return final_settings

    @property
    def evaluated_k_points(self) -> Kpoints:
        # TODO: move this to the Kpoints class
        return Kpoints(**self._evaluate_dict(self.kpoints.to_dict()))

    @classmethod
    def add_keyword_modifier(cls, keyword_modifier: callable):
        # !!! this is a copy/paste of the method from vasp.Incar
        if hasattr(cls, keyword_modifier.__name__):
            raise Exception(
                "The Incar class already has a modifier with this name. "
                "Please use a different modifier name to avoid conflicts."
            )
        setattr(cls, keyword_modifier.__name__, staticmethod(keyword_modifier))


# set some default keyword modifiers
for modifier in [
    keyword_modifier_pseudo_dir,
    keyword_modifier_nat,
    keyword_modifier_ntyp,
    keyword_modifier_ecutwfc,
    keyword_modifier_ecutrho,
]:
    PwscfInput.add_keyword_modifier(modifier)
