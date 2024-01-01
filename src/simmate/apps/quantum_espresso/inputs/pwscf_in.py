# -*- coding: utf-8 -*-

# Alternative implementations of this class from ASE and PyMatGen
# https://gitlab.com/ase/ase/-/blob/master/ase/io/espresso.py
# https://github.com/materialsproject/pymatgen/blob/master/pymatgen/io/pwscf.py

from pathlib import Path

from pymatgen.core import Element, Lattice  # TODO: replace with toolkit objs

from simmate.toolkit import Structure
from simmate.utilities import str_to_datatype

# TODO: add/merge functionality of kw modifiers from INCAR
# from simmate.apps.vasp.inputs.incar_modifiers import ....


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
        pseudo: str | Path = None,
        # sections of input file
        # TODO: should these just be a single dictionary?
        control: dict = {"calculation": "scf"},
        system: dict = {},
        electrons: dict = {},
        ions: dict = {},
        cell: dict = {},
        # kpts settings
        # TODO: replace with Kpoints class
        kpoints_mode: str = "automatic",
        kpoints_grid: tuple[int] = (1, 1, 1),
        kpoints_shift: tuple[float] = (0, 0, 0),
    ):
        """
        Initializes a PWSCF input file.

        Args:
            structure (Structure): Input structure. For spin-polarized calculation,
                properties (e.g. {"starting_magnetization": -0.5,
                "pseudo": "Mn.pbe-sp-van.UPF"}) on each site is needed instead of
                pseudo (dict).
            pseudo (dict): A dict of the pseudopotentials to use. Default to None.
            control (dict): Control parameters. Refer to official PWSCF doc
                on supported parameters. Default to {"calculation": "scf"}
            system (dict): System parameters. Refer to official PWSCF doc
                on supported parameters. Default to None, which means {}.
            electrons (dict): Electron parameters. Refer to official PWSCF doc
                on supported parameters. Default to None, which means {}.
            ions (dict): Ions parameters. Refer to official PWSCF doc
                on supported parameters. Default to None, which means {}.
            cell (dict): Cell parameters. Refer to official PWSCF doc
                on supported parameters. Default to None, which means {}.
            kpoints_mode (str): Kpoints generation mode. Default to automatic.
            kpoints_grid (sequence): The kpoint grid. Default to (1, 1, 1).
            kpoints_shift (sequence): The shift for the kpoints. Defaults to
                (0, 0, 0).
        """
        self.structure = structure
        self.pseudo = pseudo
        self.kpoints_mode = kpoints_mode
        self.kpoints_grid = kpoints_grid
        self.kpoints_shift = kpoints_shift

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
                    )

            # All other sections need special handling

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

            elif section.startswith("K_POINTS") or section.startswith(
                "ADDITIONAL_K_POINTS"
            ):
                section_name, *section_mode = section.lower().split()
                if not section_mode:
                    section_mode = "tpiba"  # using default value
                section_data = {
                    "mode": section_mode,
                    "data": [],
                }
                if section_mode == "gamma":
                    raise NotImplementedError()  # TODO
                elif section_mode == "automatic":
                    raise NotImplementedError()  # TODO
                elif section_mode in [
                    "tpiba",
                    "crystal",
                    "tpiba_b",
                    "crystal_b",
                    "tpiba_c",
                    "crystal_c",
                ]:
                    # The first line is always just the total number of kpts.
                    # Then each line follows...
                    #   xk_x(1) 	 xk_y(1) 	 xk_z(1) 	 wk(1)
                    # for ex:
                    #   10
                    #   0.1250000  0.1250000  0.1250000   1.00
                    #   0.1250000  0.1250000  0.3750000   3.00
                    #   ..... (+ 8 more lines for kpts)
                    # nkpts = line[0]  # we don't store this because it can be inferred
                    for line in lines[1:]:
                        x, y, z, weight = line.strip().split()
                        kpt = {
                            "coords": [float(x), float(y), float(z)],
                            "weight": float(weight),
                        }
                        section_data["data"].append(kpt)

            elif section.startswith("CELL_PARAMETERS"):
                section_name, *section_mode = section.lower().split()
                if not section_mode:
                    section_mode = "alat"  # using default value
                section_data = {
                    "mode": section_mode,
                    "data": [],
                }
                # section format follows...
                #   v1(1)  v1(2)  v1(3)    ... 1st lattice vector
                #   v2(1)  v2(2)  v2(3)    ... 2nd lattice vector
                #   v3(1)  v3(2)  v3(3)    ... 3rd lattice vector
                assert len(lines) == 3  # bug-check
                lattice = [float(line.strip().split()) for line in lines]
                section_data["data"].append(lattice)

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

            # regardless of the method above, we now have cleaned the section
            sections_cleaned[section_name] = section_data

        # we now have all the infomation we need in a clean dictionary format
        return sections_cleaned
        # return cls.from_dict(sections_cleaned)

    # @classmethod
    # def from_dict(cls, data: dict):

    # -------------------------------------------------------------------------

    # Export methods

    # def to_str(self) -> str:
    # def to_file(self, filename: Path | str = "settings.in"):
    # def to_dict(self) -> dict:

    # -------------------------------------------------------------------------
