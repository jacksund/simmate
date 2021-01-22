# -*- coding: utf-8 -*-

import os
import re
import warnings
from collections import OrderedDict, namedtuple
from hashlib import md5

from monty.io import zopen
from monty.json import MSONable
from monty.os.path import zpath
from monty.serialization import loadfn

from pymatgen import SETTINGS
from pymatgen.core.periodic_table import Element


def _parse_string(s):
    return "{}".format(s.strip())


def _parse_bool(s):
    m = re.match(r"^\.?([TFtf])[A-Za-z]*\.?", s)
    if m:
        return m.group(1) in ["T", "t"]
    raise ValueError(s + " should be a boolean type!")


def _parse_float(s):
    return float(re.search(r"^-?\d*\.?\d*[eE]?-?\d*", s).group(0))


def _parse_int(s):
    return int(re.match(r"^-?[0-9]+", s).group(0))


def _parse_list(s):
    return [float(y) for y in re.split(r"\s+", s.strip()) if not y.isalpha()]


Orbital = namedtuple("Orbital", ["n", "l", "j", "E", "occ"])
OrbitalDescription = namedtuple(
    "OrbitalDescription", ["l", "E", "Type", "Rcut", "Type2", "Rcut2"]
)


class UnknownPotcarWarning(UserWarning):
    """
    Warning raised when POTCAR hashes do not pass validation
    """

    pass


class PotcarSingle:
    """
    Object for a **single** POTCAR. The builder assumes the POTCAR contains
    the complete untouched data in "data" as a string and a dict of keywords.
    .. attribute:: data
        POTCAR data as a string.
    .. attribute:: keywords
        Keywords parsed from the POTCAR as a dict. All keywords are also
        accessible as attributes in themselves. E.g., potcar.enmax,
        potcar.encut, etc.
    md5 hashes of the entire POTCAR file and the actual data are validated
    against a database of known good hashes. Appropriate warnings or errors
    are raised if a POTCAR hash fails validation.
    """

    functional_dir = {
        "PBE": "POT_GGA_PAW_PBE",
        "PBE_52": "POT_GGA_PAW_PBE_52",
        "PBE_54": "POT_GGA_PAW_PBE_54",
        "LDA": "POT_LDA_PAW",
        "LDA_52": "POT_LDA_PAW_52",
        "LDA_54": "POT_LDA_PAW_54",
        "PW91": "POT_GGA_PAW_PW91",
        "LDA_US": "POT_LDA_US",
        "PW91_US": "POT_GGA_US_PW91",
        "Perdew-Zunger81": "POT_LDA_PAW",
    }

    functional_tags = {
        "pe": {"name": "PBE", "class": "GGA"},
        "91": {"name": "PW91", "class": "GGA"},
        "rp": {"name": "revPBE", "class": "GGA"},
        "am": {"name": "AM05", "class": "GGA"},
        "ps": {"name": "PBEsol", "class": "GGA"},
        "pw": {"name": "PW86", "class": "GGA"},
        "lm": {"name": "Langreth-Mehl-Hu", "class": "GGA"},
        "pb": {"name": "Perdew-Becke", "class": "GGA"},
        "ca": {"name": "Perdew-Zunger81", "class": "LDA"},
        "hl": {"name": "Hedin-Lundquist", "class": "LDA"},
        "wi": {"name": "Wigner Interpoloation", "class": "LDA"},
    }

    parse_functions = {
        "LULTRA": _parse_bool,
        "LUNSCR": _parse_bool,
        "LCOR": _parse_bool,
        "LPAW": _parse_bool,
        "EATOM": _parse_float,
        "RPACOR": _parse_float,
        "POMASS": _parse_float,
        "ZVAL": _parse_float,
        "RCORE": _parse_float,
        "RWIGS": _parse_float,
        "ENMAX": _parse_float,
        "ENMIN": _parse_float,
        "EMMIN": _parse_float,
        "EAUG": _parse_float,
        "DEXC": _parse_float,
        "RMAX": _parse_float,
        "RAUG": _parse_float,
        "RDEP": _parse_float,
        "RDEPT": _parse_float,
        "QCUT": _parse_float,
        "QGAM": _parse_float,
        "RCLOC": _parse_float,
        "IUNSCR": _parse_int,
        "ICORE": _parse_int,
        "NDATA": _parse_int,
        "VRHFIN": _parse_string,
        "LEXCH": _parse_string,
        "TITEL": _parse_string,
        "STEP": _parse_list,
        "RRKJ": _parse_list,
        "GGA": _parse_list,
    }

    def __init__(self, data, symbol=None):
        """
        Args:
            data:
                Complete and single potcar file as a string.
            symbol:
                POTCAR symbol corresponding to the filename suffix
                e.g. "Tm_3" for POTCAR.TM_3". If not given, pymatgen
                will attempt to extract the symbol from the file itself.
                However, this is not always reliable!
        """
        self.data = data  # raw POTCAR as a string

        # Vasp parses header in vasprun.xml and this differs from the titel
        self.header = data.split("\n")[0].strip()

        search_lines = re.search(
            r"(?s)(parameters from PSCTR are:" r".*?END of PSCTR-controll parameters)",
            data,
        ).group(1)

        self.keywords = {}
        for key, val in re.findall(
            r"(\S+)\s*=\s*(.*?)(?=;|$)", search_lines, flags=re.MULTILINE
        ):
            try:
                self.keywords[key] = self.parse_functions[key](val)
            except KeyError:
                warnings.warn("Ignoring unknown variable type %s" % key)

        PSCTR = OrderedDict()

        array_search = re.compile(r"(-*[0-9.]+)")
        orbitals = []
        descriptions = []
        atomic_configuration = re.search(
            r"Atomic configuration\s*\n?" r"(.*?)Description", search_lines
        )
        if atomic_configuration:
            lines = atomic_configuration.group(1).splitlines()
            num_entries = re.search(r"([0-9]+)", lines[0]).group(1)
            num_entries = int(num_entries)
            PSCTR["nentries"] = num_entries
            for line in lines[1:]:
                orbit = array_search.findall(line)
                if orbit:
                    orbitals.append(
                        self.Orbital(
                            int(orbit[0]),
                            int(orbit[1]),
                            float(orbit[2]),
                            float(orbit[3]),
                            float(orbit[4]),
                        )
                    )
            PSCTR["Orbitals"] = tuple(orbitals)

        description_string = re.search(
            r"(?s)Description\s*\n"
            r"(.*?)Error from kinetic"
            r" energy argument \(eV\)",
            search_lines,
        )
        if description_string:
            for line in description_string.group(1).splitlines():
                description = array_search.findall(line)
                if description:
                    descriptions.append(
                        OrbitalDescription(
                            int(description[0]),
                            float(description[1]),
                            int(description[2]),
                            float(description[3]),
                            int(description[4]) if len(description) > 4 else None,
                            float(description[5]) if len(description) > 4 else None,
                        )
                    )

        if descriptions:
            PSCTR["OrbitalDescriptions"] = tuple(descriptions)

        rrkj_kinetic_energy_string = re.search(
            r"(?s)Error from kinetic energy argument \(eV\)\s*\n"
            r"(.*?)END of PSCTR-controll parameters",
            search_lines,
        )
        rrkj_array = []
        if rrkj_kinetic_energy_string:
            for line in rrkj_kinetic_energy_string.group(1).splitlines():
                if "=" not in line:
                    rrkj_array += _parse_list(line.strip("\n"))
            if rrkj_array:
                PSCTR["RRKJ"] = tuple(rrkj_array)

        PSCTR.update(self.keywords)
        self.PSCTR = OrderedDict(sorted(PSCTR.items(), key=lambda x: x[0]))

        if symbol:
            self._symbol = symbol
        else:
            try:
                self._symbol = self.keywords["TITEL"].split(" ")[1].strip()
            except IndexError:
                self._symbol = self.keywords["TITEL"].strip()

        # Compute the POTCAR hashes and check them against the database of known
        # VASP POTCARs
        self.hash = self.get_potcar_hash()
        self.file_hash = self.get_potcar_file_hash()

        if self.identify_potcar(mode="data")[0] == []:
            warnings.warn(
                "POTCAR data with symbol {} does not match any VASP\
                          POTCAR known to pymatgen. We advise verifying the\
                          integrity of your POTCAR files.".format(
                    self.symbol
                ),
                UnknownPotcarWarning,
            )
        elif self.identify_potcar(mode="file")[0] == []:
            warnings.warn(
                "POTCAR with symbol {} has metadata that does not match\
                          any VASP POTCAR known to pymatgen. The data in this\
                          POTCAR is known to match the following functionals:\
                          {}".format(
                    self.symbol, self.identify_potcar(mode="data")[0]
                ),
                UnknownPotcarWarning,
            )

    def __str__(self):
        return self.data + "\n"

    @property
    def electron_configuration(self):
        """
        :return: Electronic configuration of the PotcarSingle.
        """
        if not self.nelectrons.is_integer():
            warnings.warn(
                "POTCAR has non-integer charge, "
                "electron configuration not well-defined."
            )
            return None
        el = Element.from_Z(self.atomic_no)
        full_config = el.full_electronic_structure
        nelect = self.nelectrons
        config = []
        while nelect > 0:
            e = full_config.pop(-1)
            config.append(e)
            nelect -= e[-1]
        return config

    def write_file(self, filename: str) -> None:
        """
        Writes PotcarSingle to a file.
        :param filename: Filename
        """
        with zopen(filename, "wt") as f:
            f.write(self.__str__())

    @staticmethod
    def from_file(filename: str) -> "PotcarSingle":
        """
        Reads PotcarSingle from file.
        :param filename: Filename.
        :return: PotcarSingle.
        """
        match = re.search(r"(?<=POTCAR\.)(.*)(?=.gz)", str(filename))
        if match:
            symbol = match.group(0)
        else:
            symbol = ""

        try:
            with zopen(filename, "rt") as f:
                return PotcarSingle(f.read(), symbol=symbol or None)
        except UnicodeDecodeError:
            warnings.warn(
                "POTCAR contains invalid unicode errors. "
                "We will attempt to read it by ignoring errors."
            )
            import codecs

            with codecs.open(filename, "r", encoding="utf-8", errors="ignore") as f:
                return PotcarSingle(f.read(), symbol=symbol or None)

    @staticmethod
    def from_symbol_and_functional(symbol: str, functional: str = None):
        """
        Makes a PotcarSingle from a symbol and functional.
        :param symbol: Symbol, e.g., Li_sv
        :param functional: E.g., PBE
        :return: PotcarSingle
        """
        if functional is None:
            functional = SETTINGS.get("PMG_DEFAULT_FUNCTIONAL", "PBE")
        funcdir = PotcarSingle.functional_dir[functional]
        d = SETTINGS.get("PMG_VASP_PSP_DIR")
        if d is None:
            raise ValueError(
                "No POTCAR for %s with functional %s found. "
                "Please set the PMG_VASP_PSP_DIR environment in "
                ".pmgrc.yaml, or you may need to set "
                "PMG_DEFAULT_FUNCTIONAL to PBE_52 or PBE_54 if you "
                "are using newer psps from VASP." % (symbol, functional)
            )
        paths_to_try = [
            os.path.join(d, funcdir, "POTCAR.{}".format(symbol)),
            os.path.join(d, funcdir, symbol, "POTCAR"),
        ]
        for p in paths_to_try:
            p = os.path.expanduser(p)
            p = zpath(p)
            if os.path.exists(p):
                psingle = PotcarSingle.from_file(p)
                return psingle
        raise IOError(
            "You do not have the right POTCAR with functional "
            + "{} and label {} in your VASP_PSP_DIR".format(functional, symbol)
        )

    @property
    def element(self):
        """
        Attempt to return the atomic symbol based on the VRHFIN keyword.
        """
        element = self.keywords["VRHFIN"].split(":")[0].strip()
        try:
            return Element(element).symbol
        except ValueError:
            # VASP incorrectly gives the element symbol for Xe as "X"
            # Some potentials, e.g., Zr_sv, gives the symbol as r.
            if element == "X":
                return "Xe"
            return Element(self.symbol.split("_")[0]).symbol

    @property
    def atomic_no(self) -> int:
        """
        Attempt to return the atomic number based on the VRHFIN keyword.
        """
        return Element(self.element).Z

    @property
    def nelectrons(self):
        """
        :return: Number of electrons
        """
        return self.zval

    @property
    def symbol(self):
        """
        :return: The POTCAR symbol, e.g. W_pv
        """
        return self._symbol

    @property
    def potential_type(self) -> str:
        """
        :return: Type of PSP. E.g., US, PAW, etc.
        """
        if self.lultra:
            return "US"
        if self.lpaw:
            return "PAW"
        return "NC"

    @property
    def functional(self):
        """
        :return: Functional associated with PotcarSingle.
        """
        return self.functional_tags.get(self.LEXCH.lower(), {}).get("name")

    @property
    def functional_class(self):
        """
        :return: Functional class associated with PotcarSingle.
        """
        return self.functional_tags.get(self.LEXCH.lower(), {}).get("class")

    def identify_potcar(self, mode: str = "data"):
        """
        Identify the symbol and compatible functionals associated with this PotcarSingle.
        This method checks the md5 hash of either the POTCAR data (PotcarSingle.hash)
        or the entire POTCAR file (PotcarSingle.file_hash) against a database
        of hashes for POTCARs distributed with VASP 5.4.4.
        Args:
            mode (str): 'data' or 'file'. 'data' mode checks the hash of the POTCAR
                        data itself, while 'file' mode checks the hash of the entire
                        POTCAR file, including metadata.
        Returns:
            symbol (List): List of symbols associated with the PotcarSingle
            potcar_functionals (List): List of potcar functionals associated with
                                       the PotcarSingle
        """
        # Dict to translate the sets in the .json file to the keys used in
        # DictSet
        mapping_dict = {
            "potUSPP_GGA": {
                "pymatgen_key": "PW91_US",
                "vasp_description": "Ultrasoft pseudo potentials\
                                         for LDA and PW91 (dated 2002-08-20 and 2002-04-08,\
                                         respectively). These files are outdated, not\
                                         supported and only distributed as is.",
            },
            "potUSPP_LDA": {
                "pymatgen_key": "LDA_US",
                "vasp_description": "Ultrasoft pseudo potentials\
                                         for LDA and PW91 (dated 2002-08-20 and 2002-04-08,\
                                         respectively). These files are outdated, not\
                                         supported and only distributed as is.",
            },
            "potpaw_GGA": {
                "pymatgen_key": "PW91",
                "vasp_description": "The LDA, PW91 and PBE PAW datasets\
                                        (snapshot: 05-05-2010, 19-09-2006 and 06-05-2010,\
                                        respectively). These files are outdated, not\
                                        supported and only distributed as is.",
            },
            "potpaw_LDA": {
                "pymatgen_key": "Perdew-Zunger81",
                "vasp_description": "The LDA, PW91 and PBE PAW datasets\
                                        (snapshot: 05-05-2010, 19-09-2006 and 06-05-2010,\
                                        respectively). These files are outdated, not\
                                        supported and only distributed as is.",
            },
            "potpaw_LDA.52": {
                "pymatgen_key": "LDA_52",
                "vasp_description": "LDA PAW datasets version 52,\
                                           including the early GW variety (snapshot 19-04-2012).\
                                           When read by VASP these files yield identical results\
                                           as the files distributed in 2012 ('unvie' release).",
            },
            "potpaw_LDA.54": {
                "pymatgen_key": "LDA_54",
                "vasp_description": "LDA PAW datasets version 54,\
                                           including the GW variety (original release 2015-09-04).\
                                           When read by VASP these files yield identical results as\
                                           the files distributed before.",
            },
            "potpaw_PBE": {
                "pymatgen_key": "PBE",
                "vasp_description": "The LDA, PW91 and PBE PAW datasets\
                                        (snapshot: 05-05-2010, 19-09-2006 and 06-05-2010,\
                                        respectively). These files are outdated, not\
                                        supported and only distributed as is.",
            },
            "potpaw_PBE.52": {
                "pymatgen_key": "PBE_52",
                "vasp_description": "PBE PAW datasets version 52,\
                                           including early GW variety (snapshot 19-04-2012).\
                                           When read by VASP these files yield identical\
                                           results as the files distributed in 2012.",
            },
            "potpaw_PBE.54": {
                "pymatgen_key": "PBE_54",
                "vasp_description": "PBE PAW datasets version 54,\
                                           including the GW variety (original release 2015-09-04).\
                                           When read by VASP these files yield identical results as\
                                           the files distributed before.",
            },
            "unvie_potpaw.52": {
                "pymatgen_key": "unvie_LDA_52",
                "vasp_description": "files released previously\
                                             for vasp.5.2 (2012-04) and vasp.5.4 (2015-09-04)\
                                             by univie.",
            },
            "unvie_potpaw.54": {
                "pymatgen_key": "unvie_LDA_54",
                "vasp_description": "files released previously\
                                             for vasp.5.2 (2012-04) and vasp.5.4 (2015-09-04)\
                                             by univie.",
            },
            "unvie_potpaw_PBE.52": {
                "pymatgen_key": "unvie_PBE_52",
                "vasp_description": "files released previously\
                                                for vasp.5.2 (2012-04) and vasp.5.4 (2015-09-04)\
                                                by univie.",
            },
            "unvie_potpaw_PBE.54": {
                "pymatgen_key": "unvie_PBE_52",
                "vasp_description": "files released previously\
                                                for vasp.5.2 (2012-04) and vasp.5.4 (2015-09-04)\
                                                by univie.",
            },
        }

        cwd = os.path.abspath(os.path.dirname(__file__))

        if mode == "data":
            hash_db = loadfn(os.path.join(cwd, "vasp_potcar_pymatgen_hashes.json"))
            potcar_hash = self.hash
        elif mode == "file":
            hash_db = loadfn(os.path.join(cwd, "vasp_potcar_file_hashes.json"))
            potcar_hash = self.file_hash
        else:
            raise ValueError("Bad 'mode' argument. Specify 'data' or 'file'.")

        identity = hash_db.get(potcar_hash)

        if identity:
            # convert the potcar_functionals from the .json dict into the functional
            # keys that pymatgen uses
            potcar_functionals = []
            for i in identity["potcar_functionals"]:
                potcar_functionals.append(mapping_dict[i]["pymatgen_key"])
            potcar_functionals = list(set(potcar_functionals))

            return potcar_functionals, identity["potcar_symbols"]
        return [], []

    def get_potcar_file_hash(self):
        """
        Computes a hash of the entire PotcarSingle.
        This hash corresponds to the md5 hash of the POTCAR file itself.
        :return: Hash value.
        """
        return md5(self.data.encode("utf-8")).hexdigest()

    def get_potcar_hash(self):
        """
        Computes a md5 hash of the data defining the PotcarSingle.
        :return: Hash value.
        """
        hash_str = ""
        for k, v in self.PSCTR.items():
            hash_str += "{}".format(k)
            if isinstance(v, int):
                hash_str += "{}".format(v)
            elif isinstance(v, float):
                hash_str += "{:.3f}".format(v)
            elif isinstance(v, bool):
                hash_str += "{}".format(bool)
            elif isinstance(v, (tuple, list)):
                for item in v:
                    if isinstance(item, float):
                        hash_str += "{:.3f}".format(item)
                    elif isinstance(item, (Orbital, OrbitalDescription)):
                        for item_v in item:
                            if isinstance(item_v, (int, str)):
                                hash_str += "{}".format(item_v)
                            elif isinstance(item_v, float):
                                hash_str += "{:.3f}".format(item_v)
                            else:
                                hash_str += "{}".format(item_v) if item_v else ""
            else:
                hash_str += v.replace(" ", "")

        self.hash_str = hash_str
        return md5(hash_str.lower().encode("utf-8")).hexdigest()

    def __getattr__(self, a):
        """
        Delegates attributes to keywords. For example, you can use
        potcarsingle.enmax to get the ENMAX of the POTCAR.
        For float type properties, they are converted to the correct float. By
        default, all energies in eV and all length scales are in Angstroms.
        """

        try:
            return self.keywords[a.upper()]
        except Exception:
            raise AttributeError(a)


class Potcar(list, MSONable):
    """
    Object for reading and writing POTCAR files for calculations. Consists of a
    list of PotcarSingle.
    """

    FUNCTIONAL_CHOICES = list(PotcarSingle.functional_dir.keys())

    def __init__(self, symbols=None, functional=None, sym_potcar_map=None):
        """
        Args:
            symbols ([str]): Element symbols for POTCAR. This should correspond
                to the symbols used by VASP. E.g., "Mg", "Fe_pv", etc.
            functional (str): Functional used. To know what functional options
                there are, use Potcar.FUNCTIONAL_CHOICES. Note that VASP has
                different versions of the same functional. By default, the old
                PBE functional is used. If you want the newer ones, use PBE_52 or
                PBE_54. Note that if you intend to compare your results with the
                Materials Project, you should use the default setting. You can also
                override the default by setting PMG_DEFAULT_FUNCTIONAL in your
                .pmgrc.yaml.
            sym_potcar_map (dict): Allows a user to specify a specific element
                symbol to raw POTCAR mapping.
        """
        if functional is None:
            functional = SETTINGS.get("PMG_DEFAULT_FUNCTIONAL", "PBE")
        super().__init__()
        self.functional = functional
        if symbols is not None:
            self.set_symbols(symbols, functional, sym_potcar_map)

    @staticmethod
    def from_file(filename: str):
        """
        Reads Potcar from file.
        :param filename: Filename
        :return: Potcar
        """
        try:
            with zopen(filename, "rt") as f:
                fdata = f.read()
        except UnicodeDecodeError:
            warnings.warn(
                "POTCAR contains invalid unicode errors. "
                "We will attempt to read it by ignoring errors."
            )
            import codecs

            with codecs.open(filename, "r", encoding="utf-8", errors="ignore") as f:
                fdata = f.read()

        potcar = Potcar()
        potcar_strings = re.compile(r"\n?(\s*.*?End of Dataset)", re.S).findall(fdata)
        functionals = []
        for p in potcar_strings:
            single = PotcarSingle(p)
            potcar.append(single)
            functionals.append(single.functional)
        if len(set(functionals)) != 1:
            raise ValueError("File contains incompatible functionals!")
        potcar.functional = functionals[0]
        return potcar

    def __str__(self):
        return "\n".join([str(potcar).strip("\n") for potcar in self]) + "\n"

    def write_file(self, filename):
        """
        Write Potcar to a file.
        Args:
            filename (str): filename to write to.
        """
        with zopen(filename, "wt") as f:
            f.write(self.__str__())

    @property
    def symbols(self):
        """
        Get the atomic symbols of all the atoms in the POTCAR file.
        """
        return [p.symbol for p in self]

    @symbols.setter
    def symbols(self, symbols):
        self.set_symbols(symbols, functional=self.functional)

    @property
    def spec(self):
        """
        Get the atomic symbols and hash of all the atoms in the POTCAR file.
        """
        return [{"symbol": p.symbol, "hash": p.get_potcar_hash()} for p in self]

    def set_symbols(self, symbols, functional=None, sym_potcar_map=None):
        """
        Initialize the POTCAR from a set of symbols. Currently, the POTCARs can
        be fetched from a location specified in .pmgrc.yaml. Use pmg config
        to add this setting.
        Args:
            symbols ([str]): A list of element symbols
            functional (str): The functional to use. If None, the setting
                PMG_DEFAULT_FUNCTIONAL in .pmgrc.yaml is used, or if this is
                not set, it will default to PBE.
            sym_potcar_map (dict): A map of symbol:raw POTCAR string. If
                sym_potcar_map is specified, POTCARs will be generated from
                the given map data rather than the config file location.
        """
        del self[:]
        if sym_potcar_map:
            for el in symbols:
                self.append(PotcarSingle(sym_potcar_map[el]))
        else:
            for el in symbols:
                p = PotcarSingle.from_symbol_and_functional(el, functional)
                self.append(p)
