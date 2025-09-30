# -*- coding: utf-8 -*-

import logging
import os
import re
import sys
import urllib.parse
from functools import cached_property
from pathlib import Path

import numpy
import pandas
from rdkit import RDLogger
from rdkit.Chem import (
    AllChem,
    Descriptors,
    Draw,
    RDConfig,
    rdmolops,
    rdqueries,
    rdRGroupDecomposition,
)
from rdkit.Chem.Draw import IPythonConsole
from rdkit.Chem.Scaffolds import MurckoScaffold

# Automatically enable common settings for molecule printing
IPythonConsole.ipython_useSVG = True

# Disable rdkit logging which can be overwhelming when loading >1k molecules
#   https://github.com/rdkit/rdkit/issues/2683
RDLogger.DisableLog("rdApp.*")

# This line enables the Synthetic Accessibility score
# It's very hacky not pythonic, but this is how rdkit does it...
#   https://mattermodeling.stackexchange.com/questions/8541/
sys.path.append(os.path.join(RDConfig.RDContribDir, "SA_Score"))
import sascorer  # can only be imported after the line above


class Molecule:
    """
    The base class for molecules, which includes information about:
        - atoms
        - atom coordinates
        - atom properties (e.g. charge)
        - bonding & stereochemistry
        - metadata (if read from SDF files)

    As a note for advanced users...

    In many cases, this class acts a python wrapper around RDkit's AllChem.Mol class.
    The Mol class is not pythonic, so the API is difficult to lookup and follow.
    This class wraps the many RDkit methods to make pythonic features easier to
    use (such as autocompletion and inspection).
    """

    rdkit_molecule: AllChem.Mol = None
    """
    The molecule as a RDkit `Mol` object.
    
    NOTE: this should rarely be used outside of Simmate's internal methods.
    Users should prefer the `to_rdkit()` method for access.
    """

    def __init__(self, rdkit_molecule: AllChem.Mol):
        """
        Establishes a new `Molecule` object as well as performs several
        checks & setup steps.

        NOTE: users should instead use the `from_*` (such as `from_smiles`)
        methods to initialize new `Molecule` object.
        """
        assert isinstance(rdkit_molecule, AllChem.Mol)

        self.rdkit_molecule = rdkit_molecule

        if not self.num_atoms:
            raise Exception("Empty molecule! Not allowed")

    def __repr__(self):
        """
        Defines what `print(molecule)` produces.

        The SDF string is given because it contains 3D coordinates which
        may be important in analysis.
        """
        return self.to_sdf()

    def __str__(self):
        """
        Defines what `str(molecule)` produces.

        The SDF string is given because it contains 3D coordinates which
        may be important in analysis.
        """
        return self.to_sdf()

    def __add__(self, molecule_to_add):
        """
        Defines what 'molecule1 + molecule2' produces. This combines the
        molecules and returns a new Molecule obj.
        """
        new_rdkt_mol = AllChem.CombineMols(
            self.rdkit_molecule,
            molecule_to_add.rdkit_molecule,
        )
        return self.__class__(new_rdkt_mol)

    def __radd__(self, other):
        """
        Defines behavior of `sum(molecules)`. This combines all molecules and
        returns a new Molecule object
        """
        # Code is from...
        # https://stackoverflow.com/questions/51036121/
        if other == 0:
            return self
        else:
            return self.__add__(other)

    def __eq__(self, other):
        """
        Defines behavior of `molecule1 == molecule2`. Note that is a very strict
        definition that uses inchi keys to establish equivalence. 2D or 3D coordinates
        as well as metadata are not taken into account.

        For a more robust comparison, you may want to compare sdf strings:
            self.to_sdf() == other.to_sdf()
        """
        if not isinstance(other, self.__class__):
            return False  # catches things like `molecule == None`
        return self.to_inchi_key() == other.to_inchi_key()

    @property
    def image(self):
        """
        Prints an image of the molecule if using an iPython-based console
        (e.g. iPython, Spyder IDE, Jupyter Notebook, etc.)
        """
        # hacky way of doing this... it really just returns the rdkit_molecule
        return self.rdkit_molecule

    # -------------------------------------------------------------------------

    # FIXING PROBLEMATIC INPUTS
    # see https://www.rdkit.org/docs/Cookbook.html#error-messages

    def _load_rdkit(rdkit_loader: callable, molecule_input: any, **kwargs):
        # ex:
        #   rdkit_loader = AllChem.MolFromSmiles
        #   molecule_input = "CN(C)(C)C"

        # if the input doesn't have any errors, then this is the only
        # line we need. But in many cases, this returns None becuase
        # the input is broken
        rdkit_molecule = rdkit_loader(molecule_input, **kwargs)
        if rdkit_molecule is not None:
            return rdkit_molecule

        # rdkit doesn't raise an error when it fails to read an input
        # so we therefore need to catch & retry for errors here.
        # BUG: we need to make sure sanitize isn't passed twice
        rdkit_molecule = rdkit_loader(molecule_input, sanitize=False, **kwargs)
        problems = AllChem.DetectChemistryProblems(rdkit_molecule)

        # otherwise why are we at this point in the script?
        assert len(problems) > 0

        # partially populate attributes so we can manually sanitize it below
        rdkit_molecule.UpdatePropertyCache(strict=False)

        for problem in problems:
            problem_type = problem.GetType()
            if problem_type == "AtomValenceException":
                # grab the problematic atom and key info needed to fix it
                error_atom = rdkit_molecule.GetAtomWithIdx(problem.GetAtomIdx())
                symbol = error_atom.GetSymbol()
                charge = error_atom.GetFormalCharge()
                total_valence = error_atom.GetTotalValence()

                # If user didn't include formal charges, we update them here.

                # WARNING: These are naive formal charge estimates based solely
                # on atom symbol and total valence.
                # They do NOT account for resonance, aromaticity, hypervalency,
                # radicals, or unusual bonding environments.
                # These rules may fail for many real-world molecules, especially
                # those with delocalized charges or non-standard valences.
                # Use only for basic error correction or as a last resort
                # when explicit formal charges are missing.

                # Define naive formal charge rules:
                # (symbol, total_valence): expected_charge
                formal_charge_rules = {
                    ("N", 4): 1,  # Ammonium-like N
                    ("N", 5): 2,  # Nitroso/nitrite-like N
                    ("N", 1): -3,  # Nitride-like N
                    ("O", 3): 1,  # Oxonium-like O
                    ("O", 1): -1,  # Peroxide-like O
                    ("P", 5): 0,  # Phosphonium-like P  (1?)
                    ("P", 6): 3,  # Hypothetical hypervalent  (2?)
                    ("P", 7): 3,  # Hypothetical hypervalent P
                    ("C", 4): 1,  # Carbenium ion C
                    ("C", 2): -1,  # Carbanion C
                    ("As", 5): 1,  # Arsonium-like As
                    ("As", 6): 3,  # Hypothetical hypervalent As (2?)
                    ("Sb", 5): 1,  # Stibonium-like Sb
                    ("Sb", 6): 2,  # Hexacoordinate Sb ([SbF6]-)
                    ("Sb", 7): 3,  # Hypothetical hypervalent Sb
                    ("As", 7): 3,  # Hypothetical hypervalent
                    ("Si", 5): 2,  # Pentacoordinate Si (rare)  (1?)
                    ("Si", 6): 2,  # Hexacoordinate Si ([SiF6]2-)
                    ("Al", 4): -1,  # Tetrahedral Al ([AlH4]-)
                    ("Al", 6): -3,  # Hexacoordinate Al ([AlF6]3-)
                    ("In", 4): -1,  # Tetrahedral In ([InH4]-)
                    ("In", 6): -3,  # Hexacoordinate In ([InF6]3-)
                    ("Sn", 4): 0,  # Neutral tetravalent Sn (most common, e.g., in SnO2)
                    ("Sn", 2): -2,  # Stannide (Sn2-), rare
                    ("Sn", 5): 2,  # Pentacoordinate Sn (rare, cationic)
                    ("Sn", 6): -2,  # Hexacoordinate Sn ([SnCl6]2-)
                    ("F", 1): 0,  # Carbon-fluorine (C-F)
                }
                key = (symbol, total_valence)
                if key in formal_charge_rules:
                    expected_charge = formal_charge_rules[key]
                    if charge != expected_charge:
                        logging.warning(
                            f"WARNING: Setting formal charge {expected_charge:+d} "
                            f"on {symbol} with valence {total_valence} at atom "
                            f"index {error_atom.GetIdx()}"
                        )
                        error_atom.SetFormalCharge(expected_charge)

                # print error for us to fix / add as elif condition above
                else:
                    raise Exception(
                        f"AtomValenceException: {symbol} has a total valence "
                        f"of {total_valence} and a formal charge of {charge}, "
                        "which is not allowed. Molecule input was: "
                        f"\n {molecule_input}"
                    )

            # we don't do an "else" check, but instead just let the rdkit
            # error raise itself when we try sanitizing it below

        # now that we have (potentially) fixed the errors, let's try
        # sanitizing the molecule again.
        # This will raise an error if the molecule is still malformed.
        AllChem.SanitizeMol(rdkit_molecule)

        return rdkit_molecule

    @staticmethod
    def _clean_benchtop_conventions(smiles: str) -> str:
        """
        Converts common notations in benchtop chemistry to a SMILES/SMARTS
        format.

        For example, benchtop chemists use "R1, R2, R3" to denote R (functional)
        groups, whereas SMARTS would use "*:1, *:2, *:3" to label these atoms.
        """

        # It is common that chemist use R instead of the SMARTS standard *
        # BUG: need regex to catch when R shouldn't be replaced -- such as
        # when there is an element that starts with R
        r_elements = ["Ra", "Rn", "Re", "Rh", "Rg", "Rb", "Ru", "Rf"]
        if "R" in smiles and not any([e in smiles for e in r_elements]):

            smiles = smiles.replace("R", "*")

            # If the user set things like R1, R2, R3, etc., then we actually
            # want these changed to :1, *:2, *:3
            n = 1
            while f"*{n}" in smiles:
                smiles = smiles.replace(f"*{n}", f"*:{n}")
                n += 1

        return smiles

    @property
    def is_smarts(self):
        smiles = self.to_smiles()

        if "*" in smiles:
            return True

        # TODO: what else can I check?
        # https://www.daylight.com/dayhtml/doc/theory/theory.smarts.html

        return False

    # -------------------------------------------------------------------------

    # INPUT METHODs (STRING-TYPES)

    @classmethod
    def from_sdf(cls, sdf: str, **kwargs):
        """
        Takes an SDF string and converts it to a `Molecule` object.

        Any metadata within the SDF is also read and can be accessed with the
        the `molecule.metadata` attribute

        See also:
            - `from_sdf_file`
        """
        from simmate.toolkit.file_converters import SdfAdapter

        return SdfAdapter.get_toolkit_from_sdf_str(sdf, **kwargs)

    @classmethod
    def from_smiles(cls, smiles: str, **kwargs):
        """
        Takes a SMILES string and converts it to a `Molecule` object.

        This includes reading cxSMILES, canonical SMILES, and a variety of
        other SMILES-based formats

        See also:
            - `from_csv_file`
            - `from_smiles_file`
        """
        from simmate.toolkit.file_converters import SmilesAdapter

        return SmilesAdapter.get_toolkit_from_smiles_str(smiles, **kwargs)

    @classmethod
    def from_inchi(cls, inchi: str):
        """
        Takes an InChI string and converts it to a `Molecule` object.
        """
        rdkit_molecule = cls._load_rdkit(
            rdkit_loader=AllChem.MolFromInchi,
            molecule_input=inchi,
        )
        return cls(rdkit_molecule)

    @classmethod
    def from_mol2(cls, mol2: str):
        """
        Takes a MOL2 string and converts it to a `Molecule` object.

        See also:
            - `from_mol2_file`
        """
        rdkit_molecule = cls._load_rdkit(
            rdkit_loader=AllChem.MolFromMol2Block,
            molecule_input=mol2,
        )
        return cls(rdkit_molecule)

    @classmethod
    def from_smarts(cls, smarts: str, clean_benchtop_conventions: bool = True):
        """
        Takes a SMARTS (SMILES-like) string and converts it to a `Molecule` object.
        """
        if clean_benchtop_conventions:
            smarts = cls._clean_benchtop_conventions(smarts)
        rdkit_molecule = cls._load_rdkit(
            rdkit_loader=AllChem.MolFromSmarts,
            molecule_input=smarts,
        )
        return cls(rdkit_molecule)

    @classmethod
    def from_xyz(cls, xyz: str, **kwargs):
        """
        Takes a XYZ string and converts it to a `Molecule` object.
        """
        from simmate.toolkit.file_converters import XyzAdapter

        return XyzAdapter.get_toolkit_from_str(xyz, **kwargs)

    # -------------------------------------------------------------------------

    # INPUT METHODs (PYTHON-TYPES)

    @classmethod
    def from_rdkit(cls, rdkit_molecule: AllChem.Mol):
        """
        Takes a RDKit `Mol` object and converts it to a `Molecule` object.

        NOTE: it is often better to load molecules using it's original format,
        such as using the `from_smiles` for `from_sdf` methods.
        """
        return cls(rdkit_molecule)

    @classmethod
    def from_binary(cls, binary: str):  # is str the right type?
        """
        Takes the output from `to_binary` and/or a RDKit `Mol.ToBinary()` and
        converts it to a `Molecule` object.
        """
        return cls(AllChem.Mol(binary))

    # -------------------------------------------------------------------------

    # INPUT METHODS (FILE-BASED)

    @classmethod
    def from_file(cls, filename: str | Path, **kwargs):
        """
        Dynamically determines the file type (using it's extension) and
        calls the appropriate method to load it to a `Molecule` object.

        IMPORTANT: If you are loading files with more than 1 molecule or
        large files, the `MoleculeList` class and it's methods take preference
        over those here.
        """
        filename = Path(filename)

        if filename.suffix == ".smi":
            return cls.from_smiles_file(filename, **kwargs)

        elif filename.suffix == ".sdf":
            return cls.from_sdf_file(filename, **kwargs)

        elif filename.suffix == ".csv":
            return cls.from_csv_file(filename, **kwargs)

        elif filename.suffix == ".mol2":
            return cls.from_mol2_file(filename)

        elif filename.suffix == ".mae":
            return cls.from_mae_file(filename)

        elif filename.suffix == ".xyz":
            return cls.from_xyz_file(filename)

        elif filename.suffix == ".cxsmiles":
            raise NotImplementedError()

        elif filename.suffix == ".inchi":
            raise NotImplementedError()

        elif filename.suffix == ".mol":
            raise NotImplementedError()

        else:
            raise Exception(f"Unknown filetype provided: {filename.suffix}")

    @classmethod
    def from_sdf_file(cls, filename: str | Path, **kwargs):
        """
        Takes an SDF file (*.sdf) and converts it to a `Molecule` object.

        Any metadata within the SDF is also read and can be accessed with the
        the `molecule.metadata` attribute
        """
        from simmate.toolkit.file_converters import SdfAdapter

        return SdfAdapter.get_toolkits_from_sdf_file(filename, **kwargs)

    @classmethod
    def from_smiles_file(cls, filename: str | Path, **kwargs):
        """
        Takes a SMILES file (*.smi) and converts it to a `Molecule` object.
        """
        from simmate.toolkit.file_converters import SmilesAdapter

        return SmilesAdapter.get_toolkits_from_smiles_file(filename, **kwargs)

    @classmethod
    def from_mol2_file(cls, filename: str | Path):
        """
        Takes a MOL2 file (*.mol2) and converts it to a `Molecule` object.
        """
        filename = Path(filename)
        with filename.open("r") as file:
            lines = file.read()
        delimiter = "@<TRIPOS>MOLECULE"
        mol2_strs = [delimiter + entry for entry in lines.split(delimiter) if entry]
        molecules = [
            Molecule.from_mol2(mol2_str.strip()) for mol2_str in mol2_strs if mol2_str
        ]  # BUG: strip causes failures sometimes...?
        return molecules if len(molecules) > 1 else molecules[0]

    @classmethod
    def from_mae_file(cls, filename: str | Path, **kwargs):
        """
        Takes a Schrodinger Maestro file (*.mae) and converts it to
        a `Molecule` object.
        """
        from simmate.toolkit.file_converters import MaeAdapter

        return MaeAdapter.get_toolkits_from_file(filename, **kwargs)

    @classmethod
    def from_csv_file(
        cls,
        filename: str,
        column_name: str,
        column_type: str = "smiles",
        return_dataframe: bool = False,
        **kwargs,
    ):
        """
        Takes a CSV file (*.csv) and converts it to a `Molecule` object.
        The CSV column that should be read can contain any supported 'string'
        format. Optionally, the full dataset can also be returned, rather
        than a `MoleculeList` object.

        #### Parameters

        - `filename`:
            name (+ relative path) of the CSV file

        - `column_name`:
            name of the column in the CSV that contains the molecule strings

        - `column_type`:
            type of string that the `column_name` column contains. Defaults to
            'smiles'.

        - `return_dataframe`:
            Whether to return the full CSV data as dataframe with the molecules
            that have been loaded. Defaults to
            False.
        """
        df = pandas.read_csv(filename, **kwargs)

        # For now I just grab the molecule input strings and ignore everything
        # else. In the future, I should maybe load the whole table and attach
        # the molecule to the data (or vise versa).
        molecule_strs = df[column_name].values

        if column_type == "smiles":
            molecules = [
                cls.from_smiles(molecule_str) for molecule_str in molecule_strs
            ]
        # TODO: support other input types like inchi, sdf, or dynamic
        else:
            raise Exception(f"Unsupported column type: {column_type}")

        # TODO: maybe add molecules to the dataframe as a 'simmate_molecules' col?
        return (df, molecules) if return_dataframe else molecules

    # -------------------------------------------------------------------------

    # DYNAMIC INPUT

    @classmethod
    def from_dynamic(cls, molecule: str):
        """
        Dynamically determines the input type (e.g. is it a sdf file? a smiles
        string? etc.) and calls the appropriate method to load it to
        a `Molecule` object.

        NOTE: this is meant for top-level inputs (e.g. workflows) and for beginners.
        It will always be faster (and more robust) to call your known method
        directly -- i.e. if you know you have a SMILES string, just call
        `from_smiles` instead of this method.
        """
        # if the input is already a toolkit molecule, just return it back
        if isinstance(molecule, cls):
            return molecule

        elif isinstance(molecule, bytes):
            return cls.from_binary(molecule)

        # if the string contains an "END" then we have an SDF
        elif isinstance(molecule, str) and ("END" in molecule or "$$$$" in molecule):
            return cls.from_sdf(molecule)

        # if the string contains an "END" then we have an SDF
        elif isinstance(molecule, str) and molecule.startswith("InChI="):
            return cls.from_inchi(molecule)

        # if the value is a str and it relates to a filepath, then we load the
        # structure from a file.
        elif isinstance(molecule, str) and any(
            [
                molecule.endswith(ext)
                for ext in [
                    ".smi",
                    ".sdf",
                    ".inchi",
                    ".cxsmiles",
                    ".mol",
                    ".mol2",
                ]
            ]
        ):
            if Path(molecule).exists():
                return cls.from_file(molecule)
            else:
                raise FileNotFoundError(
                    "Are you trying to provide a filename as your input molecule? "
                    "If so, make sure you have the proper working directory set. "
                    f"We were unable to find '{molecule}' in '{Path.cwd()}'"
                )

        # there's no clear sign that we have a SMILES string or not, so we
        # just try and see if it works
        # OPTIMIZE: what check could we try instead? This might be the most
        # common input so we should either move this up or have a smarter check
        elif isinstance(molecule, str):
            try:
                return cls.from_smiles(molecule)
            except:
                raise Exception("Unknown string format OR incorrect smiles.")

        # If we have a list, then we likely have a list of molecules, where
        # we can do a recursive call to this function for each one.
        elif isinstance(molecule, list):
            return [cls.from_dynamic(entry) for entry in molecule]

        # Otherwise an incorrect format was given
        else:
            raise Exception(
                "Unknown format provided for molecule input. "
                f"{type(molecule)} was provided."
            )

    # -------------------------------------------------------------------------

    # OUTPUT METHODS

    def to_sdf(self, include_metadata: bool = False) -> str:
        """
        Converts the current `Molecule` object to an SDF string
        """
        sdf = AllChem.MolToMolBlock(self.rdkit_molecule)

        if include_metadata and self.metadata:
            for key, value in self.metadata.items():
                sdf += f"\n>  <{key}>\n{value}\n"

        sdf += "\n$$$$\n"
        return sdf

    def to_smiles(
        self,
        remove_hydrogen: bool = True,
        kekulize: bool = False,
    ) -> str:
        """
        Converts the current `Molecule` object to a SMILES string

        #### Parameters

        - `remove_hydrogen`:
            Whether to remove implicit hydrogens from the molecule before writing.
            Defaults to True as this is the cleaner and smaller string

        - `kekulize`:
            Whether to convert the SMILES string to the kekulized form -- i.e.
            whether aromatic bonds are explicitly draw.
            Defaults to False as we preferred the canonical form, though benchtop
            chemists tend to prefer the kekulized form.
        """
        return (
            AllChem.MolToSmiles(
                AllChem.RemoveHs(self.rdkit_molecule),
                kekuleSmiles=kekulize,
            )
            if remove_hydrogen
            else AllChem.MolToSmiles(
                self.rdkit_molecule,
                kekuleSmiles=kekulize,
            )
        )

    def to_cx_smiles(self) -> str:
        """
        Converts the current `Molecule` object to a cx-SMILES string
        """
        return AllChem.MolToCXSmiles(self.rdkit_molecule)

    def to_inchi(self, remove_hydrogen: bool = True) -> str:
        """
        Converts the current `Molecule` object to an INCHI string
        """
        return (
            AllChem.MolToInchi(AllChem.RemoveHs(self.rdkit_molecule))
            if remove_hydrogen
            else AllChem.MolToInchi(self.rdkit_molecule)
        )

    def to_inchi_key(self, remove_hydrogen: bool = True) -> str:
        """
        Converts the current `Molecule` object to an INCHI key string
        """
        return (
            AllChem.MolToInchiKey(AllChem.RemoveHs(self.rdkit_molecule))
            if remove_hydrogen
            else AllChem.MolToInchiKey(self.rdkit_molecule)
        )

    # -------------------------------------------------------------------------

    # PYTHON OBJECT OUTPUT METHODS

    def to_binary(self) -> str:  # !!! I don't think str is the right type here
        """
        Converts the current `Molecule` object to a binary string.

        This can be thought of as efficiently "pickling" your object, which
        can later be read back into python with `from_binary`
        """
        return self.rdkit_molecule.ToBinary()

    def to_rdkit(self) -> AllChem.Mol:
        """
        Converts the current `Molecule` object to a RDKit `Mol` object.
        """
        # BUG: should I return a deepcopy? Is that even possible with RDKit
        # C++ pointers?
        return self.rdkit_molecule

    def to_png(self):
        """
        Generates a PIL image object. Use `to_png_file` if you instead want to
        write the image directly to a file.
        """
        return Draw.MolToImage(self.rdkit_molecule)

    def to_svg(self, url_encode: bool = False, size=(300, 300)):
        """
        Generates a PIL image object. Use `to_png_file` if you instead want to
        write the image directly to a file.
        """
        if not url_encode:
            return Draw.MolToImage(
                self.rdkit_molecule,
                size=size,
                useSVG=True,
            )  # gives a PIL obj
        else:
            # Faster method for generating SVGs pulled from their tutorials:
            # https://github.com/rdkit/rdkit-tutorials/blob/master/notebooks/006_save_rdkit_mol_as_image.ipynb
            mol = Draw.rdMolDraw2D.PrepareMolForDrawing(self.rdkit_molecule)
            drawer = Draw.rdMolDraw2D.MolDraw2DSVG(size[0], size[1])
            drawer.DrawMolecule(mol)
            drawer.FinishDrawing()
            svg = drawer.GetDrawingText()
            # in web, I don't want the white background box. This is normally
            # present in the svg via something like...
            # <rect style='opacity:1.0;fill:#FFFFFF;stroke:none' width='300.0' height='300.0' x='0.0' y='0.0'> </rect>
            # Regular expression pattern to match the <rect> element with varying width and height
            pattern = r"<rect style='opacity:1\.0;fill:#FFFFFF;stroke:none' width='\d+(\.\d+)?' height='\d+(\.\d+)?' x='\d+(\.\d+)?' y='\d+(\.\d+)?'>\s*</rect>"
            svg = re.sub(pattern, "", svg)
            # This is the format that programs like streamlit's ImageCol expect:
            # https://docs.streamlit.io/develop/api-reference/data/st.column_config/st.column_config.imagecolumn
            svg_encoded = f"data:image/svg+xml;utf8,{urllib.parse.quote(svg)}"
            return svg_encoded

    def to_xyz(self):
        """
        Outputs the `Molecule` object to a XYZ file (*.xyz)

        Make sure you have a 3D molecule. If not, call `convert_to_3d` before
        using this method.
        """
        from simmate.toolkit.file_converters import XyzAdapter

        return XyzAdapter.to_str_from_toolkit(molecule=self)

    # -------------------------------------------------------------------------

    # FILE OUTPUT METHODS

    def to_png_file(self, filename: str | Path):
        """
        Outputs the `Molecule` object to a PNG image file. The image is drawn
        using RDkit
        """
        Draw.MolToFile(self.rdkit_molecule, str(filename))

    def to_sdf_file(self, filename: str | Path):
        """
        Outputs the `Molecule` object to a SDF file.

        NOTE: If are trying to writing more than 1 molecule to a single SDF
        file, see [[ TODO ]]. This method is only for 1 molecule per file.
        """
        filename = Path(filename)
        file_txt = self.to_sdf()
        with filename.open("w") as file:
            file.write(file_txt)

    def to_mae_file(self, filename: str | Path, **kwargs):
        """
        Outputs the `Molecule` object to a Schrodinger Maestro file (*.mae)
        """
        from simmate.toolkit.file_converters import MaeAdapter

        return MaeAdapter.to_file_from_toolkits(
            molecules=[self],
            filename=filename,
            **kwargs,
        )

    def to_xyz_file(self, filename: str | Path, **kwargs):
        """
        Outputs the `Molecule` object to a XYZ file (*.xyz)
        """
        from simmate.toolkit.file_converters import XyzAdapter

        return XyzAdapter.to_file_from_toolkit(
            molecule=self,
            filename=filename,
            **kwargs,
        )

    # -------------------------------------------------------------------------

    # CLEANING AND STANDARDIZATION

    @property
    def chemical_warnings(self) -> list[dict]:
        """
        Gives a list of chemical warnings/issues for the molecule
        """
        # TODO: merge this functionality into the `load_rdkit` method
        problems = AllChem.DetectChemistryProblems(self.rdkit_molecule)
        problems_cleaned = [
            {problem.GetType(): problem.Message()} for problem in problems
        ]
        return problems_cleaned

    def add_hydrogens(self):
        """
        Adds implicit hydrogens to the Molecule if they are missing.
        """
        self.rdkit_molecule = AllChem.AddHs(self.rdkit_molecule)

    def remove_hydrogens(self):
        """
        Removes implicit hydrogens to the Molecule if they are present.
        """
        self.rdkit_molecule = AllChem.RemoveHs(self.rdkit_molecule)

    def convert_to_3d(self, keep_hydrogen: bool = False):
        """
        Converts the molecule to a roughly-optimized 3D conformer.

        NOTES:

        1. There are many methods to generate 3D conformers. This currently
        uses RDkit's rough empirical approach, which is cheap and easy. In most
        cases this will not be sufficient for QM calculations.

        2. If you are converting many molecules to 3D, it is more efficient to
        use the `convert_to_3d` method of the `MoleculeList` class.
        """
        # Add implicit hydrogens, which are required for 3D
        self.add_hydrogens()
        # create a single conformer using ETKDG
        AllChem.EmbedMolecule(self.rdkit_molecule)
        # optimize atomic positions using empirical force field (MMFF94)
        AllChem.MMFFOptimizeMolecule(self.rdkit_molecule)
        # optionally remove hydrogen after conversion
        if not keep_hydrogen:
            self.remove_hydrogens()

    @cached_property
    def components(self):
        components_rdkit = rdmolops.GetMolFrags(self.rdkit_molecule, asMols=True)
        return [self.__class__(mol) for mol in components_rdkit]

    @property
    def largest_component(self):  # -> Molecule
        """
        If the `Molecule` object contains a mixture / several molecules, this
        will return the largest fragment / component in the mixture.
        """
        # If using rdkit entirely:
        # from rdkit.Chem.MolStandardize.rdMolStandardize import LargestFragmentChooser
        # largest_fragment = LargestFragmentChooser().choose(self.rdkit_molecule)
        # return self.__class__(largest_fragment)
        all_components = self.components
        all_counts = [c.num_atoms for c in all_components]
        largest_idx = all_counts.index(max(all_counts))
        return all_components[largest_idx]

    # -------------------------------------------------------------------------

    # METADATA

    @property
    def name(self) -> str:
        """
        The "name" of the molecule, which is listed at the top of an SDF file.

        The molecule must be loaded from an SDF format for this to be available.
        """
        return self.rdkit_molecule.GetProp("_Name", None)

    @property
    def metadata(self) -> dict:
        """
        The metadata of the molecule, which is listed at the bottom of an SDF file
        as key-value pairs.

        The molecule must be loaded from an SDF format for this to be available.
        """
        return self.rdkit_molecule.GetPropsAsDict(
            includePrivate=True,
            includeComputed=False,
        )

    def update_metadata(self, key: str, value: str):
        """
        Updates a key-value pair in the metadata.

        Note, rdkit only allows strings to be set for the values, probably to
        simplify exporting to an SDF format
        """
        self.rdkit_molecule.SetProp(key, value)

    @property
    def comment(self) -> str:
        """
        Any comments that were attached to a molecule.

        The molecule must be loaded from an SDF format for this to be available.
        """
        return self.rdkit_molecule.GetProp("_MolFileComments")

    # -------------------------------------------------------------------------

    # COMPOSITION

    @property
    def formula(self) -> str:
        """
        The chemical formula of this molecule
        """
        return AllChem.CalcMolFormula(self.rdkit_molecule)

    @property
    def elements(self) -> tuple[str]:
        """
        The unique set of elements in this molecule
        """
        # TODO: should this return a list? should it be in alphabetical order?
        elements = [atom.GetSymbol() for atom in self.rdkit_molecule.GetAtoms()]
        return set(elements)

    @property
    def is_dueterated(self) -> bool:
        """
        Whether the molecule has any Dueterium
        """
        for atom in self.rdkit_molecule.GetAtoms():
            if atom.GetAtomicNum() == 1 and atom.GetIsotope() == 2:
                # a single duet is enough to return true
                return True
        return False

    @property
    def is_dueterated_full(self) -> bool:
        """
        Whether the molecule is fully dueterated (i.e. 100% Hs are Dueterium)
        """
        if self.is_dueterated:
            for atom in self.rdkit_molecule.GetAtoms():
                if atom.GetAtomicNum() == 1 and atom.GetIsotope() == 1:
                    # a single non-D is enough to say no
                    return False
            return True
        # No D at all is an automatic no
        return False

    # -------------------------------------------------------------------------

    # MOLECULAR WEIGHT

    @property
    def molecular_weight(self) -> float:
        """
        The **average** molecular weight of the molecule, as calculated using
        average element masses.
        """
        return Descriptors.MolWt(self.rdkit_molecule)

    @property
    def molecular_weight_exact(self) -> float:
        """
        The exact molecular weight of the molecule, as calculated using
        exact elemental isotope masses.
        """
        return Descriptors.ExactMolWt(self.rdkit_molecule)

    @property
    def molecular_weight_heavy_atoms(self) -> float:
        """
        The **average** molecular weight of the molecule, as calculated using
        average element masses and ignoring all hydrogens.
        """
        return Descriptors.HeavyAtomMolWt(self.rdkit_molecule)

    # -------------------------------------------------------------------------

    # STEREOCHEM AND CONFORMATIONS

    @property
    def num_conformers(self) -> int:
        """
        The number of conformers contained within this `Molecule` object

        WARNING: This attribute is likely to become depreciated because we
        ideally want 1 molecule object = 1 conformer in the future.
        """
        return self.rdkit_molecule.GetNumConformers()

    @property
    def num_stereocenters(self) -> int:
        """
        The total number of stereocenters in the molecule
        """
        return len(self.get_stereocenters())

    def get_stereocenters(self) -> list[tuple[int, str]]:
        """
        Gives the atom number and type for each stereocenter in the molecule

        ex: will give something like `[(3, 'S'), (5, 'R')]`
        """
        # see https://rdkit.org/docs/Cookbook.html#identifying-stereochemistry
        return AllChem.FindMolChiralCenters(
            self.rdkit_molecule,
            force=True,
            includeUnassigned=True,
            useLegacyImplementation=False,
        )

    # -------------------------------------------------------------------------

    # BONDING

    @property
    def num_bonds(self) -> int:
        """
        Counts the total number of bonds in the molecule.

        Note, double & triple bonds are still counted as 1. Also, bonds involving
        Hydrogren are only counted if Hydrogens are added to the structure (i.e.
        implicit hydrogens are ignored).
        """
        return self.rdkit_molecule.GetNumBonds()

    @property
    def num_bonds_rotatable(self) -> int:
        """
        Gives the number of bonds that can rotate.

        Note, sterics are ignored when considering if a bond can rotate. This
        method is entirely based on symmetry of a bond.
        """
        return Descriptors.NumRotatableBonds(self.rdkit_molecule)

    @property
    def frac_c_sp3(self) -> float:
        """
        Gives the fraction of Carbon atoms that are sp3 hybridized
        """
        return Descriptors.FractionCSP3(self.rdkit_molecule)

    # -------------------------------------------------------------------------

    # ATOM COUNTING

    @property
    def num_atoms(self) -> int:
        """
        Counts all atoms in the molecule.

        Note, implicited Hydrogens are ignored if they are not added to the
        molecule.
        """
        return self.rdkit_molecule.GetNumAtoms()

    @property
    def num_atoms_heavy(self) -> int:
        """
        Counts all atoms in the molecule while ignoring Hydrogen
        """
        # self.rdkit_molecule.GetNumHeavyAtoms()  # alternative api
        return Descriptors.HeavyAtomCount(self.rdkit_molecule)

    @property
    def num_h_acceptors(self) -> int:
        """
        The number of Hydrogen-bond acceptors in the molecule.

        i.e. -- the number of electronegative atoms that contain a lone pair
        which can participate in a hydrogen bond. Typically N, O, and F atoms.
        """
        return Descriptors.NumHAcceptors(self.rdkit_molecule)

    @property
    def num_h_donors(self) -> int:
        """
        The number of Hydrogen-bond donors in the molecule.

        ie.e -- the number of electronegative atoms covalently bonded to a
        Hydrogen atom which can participate in a hydrogen bond.
        Typically N, O, and F atoms.
        """
        return Descriptors.NumHDonors(self.rdkit_molecule)

    @property
    def num_heteroatoms(self) -> int:
        """
        The number of atoms in the molecule that are not Carbon or Hydrogen
        """
        return Descriptors.NumHeteroatoms(self.rdkit_molecule)

    @property
    def num_c_atoms(self) -> int:
        """
        The number of Carbon atoms in the molecule
        """
        q = rdqueries.AtomNumEqualsQueryAtom(6)
        return len(self.rdkit_molecule.GetAtomsMatchingQuery(q))
        # return self.num_atoms_of_atomic_number(6)

    def get_num_atoms_of_atomic_number(self, atomic_number: int) -> int:
        """
        Counts the total number of atoms in a molecule of a specific atomic
        number.
        """
        q = rdqueries.AtomNumEqualsQueryAtom(atomic_number)
        return len(self.rdkit_molecule.GetAtomsMatchingQuery(q))

    def get_num_atoms_of_atomic_symbols(self, atomic_symbols: list[str]) -> int:
        """
        Counts the total number of atoms in a molecule of a list specific atomic
        symbols.
        """
        atom_matches = [
            1  # no need to store anything
            for atom in self.rdkit_molecule.GetAtoms()
            if atom.GetSymbol() in atomic_symbols
        ]
        return len(atom_matches)

    @property
    def num_halogen_atoms(self) -> int:
        """
        The number of halogen atoms in a molecule (F, Cl, Br, or I).
        """
        halogens = ["Cl", "Br", "I", "F"]
        return self.get_num_atoms_of_atomic_symbols(halogens)

    # -------------------------------------------------------------------------

    # ELECTRON COUNTING

    @property
    def num_electrons_valence(self) -> int:  # BUG: could this be a float?
        """
        The total number of valence electrons in the molecule
        """
        return Descriptors.NumValenceElectrons(self.rdkit_molecule)

    @property
    def num_electrons_radical(self) -> int:  # BUG: could this be a float?
        """
        The total number of radical electrons in the molecule
        """
        return Descriptors.NumRadicalElectrons(self.rdkit_molecule)

    # -------------------------------------------------------------------------

    # RINGS & AROMATICITY

    @property
    def num_rings(self) -> int:
        """
        The total number of atomic rings in the molecule
        """
        # return self.rdkit_molecule.GetRingInfo().NumRings() # alternative api
        return Descriptors.RingCount(self.rdkit_molecule)

    @property
    def num_rings_aromatic(self) -> int:
        """
        The total number of aromatic rings in the molecule
        """
        return Descriptors.NumAromaticRings(self.rdkit_molecule)

    @property
    def num_ring_families(self) -> int:
        """
        The total number of rings families in the molecule

        NOTE: RDkit does not provide a clear definition on what a "family" is.
        My best guess is a set of rings that are interoconnected
        (i.e. share at least 2 atoms) would be 1 family ring.
        """
        return self.rdkit_molecule.GetRingInfo().NumRingFamilies()

    @property
    def rings(self) -> tuple[tuple[int]]:
        """
        Gives a list of the atoms in each ring
        """
        return self.rdkit_molecule.GetRingInfo().BondRings()

    @property
    def ring_sizes(self) -> list[int]:
        """
        Gives the number of atoms in each individual ring
        """
        return [len(ring) for ring in self.rings]

    @property
    def ring_size_min(self) -> int:
        """
        The smallest ring size in terms of number of atoms
        """
        return min(self.ring_sizes) if self.ring_sizes else None

    @property
    def ring_size_max(self) -> int:
        """
        The largest ring size in terms of number of atoms
        """
        return max(self.ring_sizes) if self.ring_sizes else None

    @property
    def num_aliphatic_carbocycles(self) -> int:
        """
        The total number of aliphatic carbocycles in the molecule
        """
        return Descriptors.NumAliphaticCarbocycles(self.rdkit_molecule)

    @property
    def num_aliphatic_heterocycles(self) -> int:
        """
        The total number of aliphatic heterocycles in the molecule
        """
        return Descriptors.NumAliphaticHeterocycles(self.rdkit_molecule)

    @property
    def num_aromatic_heterocycles(self) -> int:
        """
        The total number of aromatic heterocycles in the molecule
        """
        return Descriptors.NumAromaticHeterocycles(self.rdkit_molecule)

    @property
    def num_saturated_carbocycles(self) -> int:
        """
        The total number of saturated carbocycles in the molecule
        """
        return Descriptors.NumSaturatedCarbocycles(self.rdkit_molecule)

    @property
    def num_saturated_heterocycles(self) -> int:
        """
        The total number of saturated heterocarbocycles in the molecule
        """
        return Descriptors.NumSaturatedHeterocycles(self.rdkit_molecule)

    @property
    def num_rings_saturated(self) -> int:
        """
        The total number of saturated rings in the molecule
        """
        return Descriptors.NumSaturatedRings(self.rdkit_molecule)

    # -------------------------------------------------------------------------

    # E STATE INDEX

    @property
    def max_abs_e_state_index(self) -> float:
        """
        Absolute maximum energy state
        """
        return Descriptors.MaxAbsEStateIndex(self.rdkit_molecule)

    @property
    def max_e_state_index(self) -> float:
        """
        maximum energy state
        """
        return Descriptors.MaxEStateIndex(self.rdkit_molecule)

    @property
    def min_abs_e_state_index(self) -> float:
        """
        Absolute minimum energy state
        """
        return Descriptors.MinAbsEStateIndex(self.rdkit_molecule)

    @property
    def min_e_state_index(self) -> float:
        """
        minimum energy state
        """
        return Descriptors.MinEStateIndex(self.rdkit_molecule)

    # -------------------------------------------------------------------------

    # PARTIAL CHARGES

    @property
    def max_abs_partial_charge(self) -> float:
        """
        Absolute maximum partial charge
        """
        return Descriptors.MaxAbsPartialCharge(self.rdkit_molecule)

    @property
    def max_partial_charge(self) -> float:
        """
        maximum partial charge
        """
        return Descriptors.MaxPartialCharge(self.rdkit_molecule)

    @property
    def min_abs_partial_charge(self) -> float:
        """
        Absolute minimum partial charge
        """
        return Descriptors.MinAbsPartialCharge(self.rdkit_molecule)

    @property
    def min_partial_charge(self) -> float:
        """
        minimum partial charge
        """
        return Descriptors.MinPartialCharge(self.rdkit_molecule)

    # -------------------------------------------------------------------------

    # Property Prediction

    @property
    def log_p_rdkit(self) -> float:
        """
        Estimates the LogP using RDkit.

        LogP = partition coefficient of the molecule in octanol vs. water
        """
        return Descriptors.MolLogP(self.rdkit_molecule)

    @property
    def tpsa_rdkit(self) -> float:
        """
        Estimates the topological polar surface area (TPSA) using RDkit
        """
        return Descriptors.TPSA(self.rdkit_molecule)

    @property
    def molar_refractivity_rdkit(self) -> float:
        """
        Estimates the molar refractivity (MR) using RDkit

        This is a measure of the total polarizability of a mole of a substance
        and is dependent on temperature, index of refraction, and pressure.
        """
        return Descriptors.MolMR(self.rdkit_molecule)

    @property
    def ipc(self):
        """
        unknown...
        """
        return Descriptors.Ipc(self.rdkit_molecule)

    @property
    def synthetic_accessibility(self) -> float:
        """
        Synthetic accessibility scores (SAS) are generated using the
        published method:
            http://www.jcheminf.com/content/1/1/8.

        The score is on a 1-10 scale, where lower values correspond to molecules
        that are easier to synthesize.

        This method wraps the implementation made by rdkit's "sascorer" module.
        """
        # score will be between 1 (easy to make) and 10 (very difficult to make)
        try:  # BUG: what if it's a mixture?
            return sascorer.calculateScore(self.rdkit_molecule)
        except:
            return None

    # -------------------------------------------------------------------------

    # R-group decomposition

    # BUG with typing: https://stackoverflow.com/questions/33533148/
    def get_r_groups(self, smarts) -> dict:
        """
        Given a SMARTS-query component, this will split the molecule at that
        query match location in the molecule and then return the R-groups
        that were connected to the match.
        """
        matches, failures = rdRGroupDecomposition.RGroupDecompose(
            [smarts.rdkit_molecule],
            [self.rdkit_molecule],
            # asSmiles=True,
        )

        # return None if it failed
        if not matches:
            return None

        # convert all entries from rdkit back to toolkit objects
        return {k: self.__class__(v) for k, v in matches[0].items()}

    # -------------------------------------------------------------------------

    # SUBCOMPONENT COUNTING

    @property
    def murko_scaffold(self):
        """
        Gives the Murko Scaffold of the molecule using RDKit:
            https://rdkit.org/docs/source/rdkit.Chem.Scaffolds.MurckoScaffold.html
        """
        rdkit_scaffold = MurckoScaffold.GetScaffoldForMol(self.rdkit_molecule)
        try:
            return self.__class__(rdkit_scaffold)
        except:
            # BUG: should I raise error for failed scaffolds? e.g. "CC(=O)O" gives ""
            return None

    def get_fragments(
        self,
        include_zeros: bool = False,
        is_smarts: bool = False,
    ) -> dict:
        """
        Iterates through >50 different substructure queries of different functional
        groups and counts the matches in the molecule.

        NOTE: This only uses RDkit's functional group set at the moment, but
        more will be available in the `toolkit.smarts_sets` module
        """
        # BUG-FIX: SMARTS molecules fail unless these methods are called first
        # https://github.com/rdkit/rdkit/issues/1984
        if is_smarts:
            from rdkit import Chem

            self.rdkit_molecule.UpdatePropertyCache()
            Chem.GetSymmSSSR(self.rdkit_molecule)

        results = {}

        fragment_types = [
            d for d in Descriptors.__dict__.keys() if d.startswith("fr_")
        ]  # + ["NHOHCount", "NOCount"]

        for fragment_type in fragment_types:
            analyzer = getattr(Descriptors, fragment_type)
            type_count = analyzer(self.rdkit_molecule)
            if type_count > 0 or include_zeros:
                # the [3:] removes the "fr_" from each keyword
                results[fragment_type[3:]] = type_count

        return results

    def is_smarts_match(self, smarts) -> bool:
        """
        Given a SMARTS query (built with `Molecule.from_smarts`), this will
        check if the molecule has a match to that query.
        """
        # OPTIMIZE: can also do 'self.num_smarts_match(smart) > 0'
        return self.rdkit_molecule.HasSubstructMatch(smarts.rdkit_molecule)

    def num_smarts_match(self, smarts) -> int:
        """
        Given a SMARTS query (built with `Molecule.from_smarts`), this will
        count the number of substructures matches the molecule has for that query.
        """
        return len(self.rdkit_molecule.GetSubstructMatches(smarts.rdkit_molecule))

    def num_substructure_matches(
        self,
        substructures: list,  # list[Molecule]
        use_chirality: bool = False,
    ) -> int:
        """
        Given a list of SMARTS queries (built with `Molecule.from_smarts`), this will
        count the number of substructures matches the molecule has for that query.

        ** i.e. the total count across ALL queries
        """
        matches = [
            self.rdkit_molecule.HasSubstructMatch(
                substruct.rdkit_molecule,
                useChirality=use_chirality,
            )
            for substruct in substructures
        ]
        return sum(matches)

    # -------------------------------------------------------------------------

    # Fingerprints

    # !!! OPTIMIZE: we need to better understand the performance tradeoffs
    # of dense (the default) vs sparse fingerprints. Also count vs. normal.

    @cached_property
    def fingerprint(self) -> numpy.ndarray:
        """
        Generates and caches the **simmate preferred** fingerprint.

        If you want to choose your fingerprint parameters (such as the size or
        path length), you should use `get_fingerprint` or it's underlying methods
        such as `get_topological_fingerprint`.

        This property is inteaded for beginers, as we choose basic fingerprint
        settings that work in most cases and enable other high-level features,
        such as `mol1 / mol2` -> to give similarity
        """
        # TODO: maybe add setting to allow user to configure the default fp globally
        return self.get_fingerprint("morgan", "numpy")

    def get_fingerprint(
        self,
        fingerprint_type: str = "topological",
        vector_type: str = "rdkit",
        **kwargs,
    ):
        """
        Generates a molecule fingerprint from one of several options and formats
        """

        if fingerprint_type == "topological":
            return self.get_topological_fingerprint(**kwargs)

        elif fingerprint_type in ["circular", "morgan"]:
            return self.get_morgan_fingerprint(**kwargs)

        elif fingerprint_type == "pattern":
            from ..featurizers import PatternFingerprint

            return PatternFingerprint.featurize(
                molecule=self,
                vector_type=vector_type,
                **kwargs,
            )

        else:
            raise Exception(f"Unknown fingerprint type: {type}")

    def get_topological_fingerprint(self, **kwargs):
        """
        Generates a topological fingerprint (aka RDkit fingerprint)

        Recommend similarity scoring: Tanimoto
        """
        fpgen = AllChem.GetRDKitFPGenerator(**kwargs)
        return fpgen.GetFingerprint(self.rdkit_molecule)

    def get_morgan_fingerprint(self, radius=2, size=1024, **kwargs):
        """
        Generates a morgan fingerprint (aka a circular fingerprint).

        Recommend similarity scoring: Dice
        """
        fpgen = AllChem.GetMorganGenerator(radius=radius, fpSize=size, **kwargs)
        return fpgen.GetCountFingerprint(self.rdkit_molecule)

    # -------------------------------------------------------------------------

    @property
    def atom_list(self) -> list[dict]:
        # TODO: need a base class to make these objects. Maybe use pymatgen.
        try:
            conformer = self.rdkit_molecule.GetConformer()
        except ValueError:
            raise Exception(
                "Failed to access 3D conformer. Is your molecule 3D? "
                "If not, you can use the `convert_to_3d` method to handle "
                "this for you."
            )
        return [
            {
                "index": atom.GetIdx(),
                "element": atom.GetSymbol(),
                "coords": list(conformer.GetAtomPosition(atom.GetIdx())),
            }
            for atom in self.rdkit_molecule.GetAtoms()
        ]
