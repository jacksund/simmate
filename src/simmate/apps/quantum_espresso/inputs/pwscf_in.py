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
        control: dict = None,
        system: dict = None,
        electrons: dict = None,
        ions: dict = None,
        cell: dict = None,
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
        sections = {}
        sections["control"] = control or {"calculation": "scf"}
        sections["system"] = system or {}
        sections["electrons"] = electrons or {}
        sections["ions"] = ions or {}
        sections["cell"] = cell or {}
        if pseudo is None:
            for site in structure:
                try:
                    site.properties["pseudo"]
                except KeyError:
                    raise PWInputError(f"Missing {site} in pseudo specification!")
        else:
            for species in self.structure.composition:
                if str(species) not in pseudo:
                    raise PWInputError(f"Missing {species} in pseudo specification!")
        self.pseudo = pseudo

        self.sections = sections
        self.kpoints_mode = kpoints_mode
        self.kpoints_grid = kpoints_grid
        self.kpoints_shift = kpoints_shift

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
            elif line in cls.PARAMETER_SECTIONS:
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
                sections_cleaned[section_name] = section_data

            # All other sections need special handling

        breakpoint()
        # return the final dictionary as an Incar object
        # return cls(**parameters)

    # TODO:
    # to_str
    # to_file
    # to_dict
    # from_dict
    # refactor __init__
