# -*- coding: utf-8 -*-

from pathlib import Path

from rdkit.Chem.rdmolfiles import MolFromXYZBlock, MolToXYZBlock

from simmate.toolkit import Molecule


class XyzAdapter:
    @staticmethod
    def get_toolkit_from_str(
        xyz: str,
        remove_hs: bool = True,
        **kwargs,
    ) -> Molecule:
        rdkit_molecule = Molecule._load_rdkit(
            rdkit_loader=MolFromXYZBlock,
            molecule_input=xyz,
            removeHs=remove_hs,
            **kwargs,
        )
        return Molecule(rdkit_molecule)

    @classmethod
    def get_toolkit_from_file(
        cls,
        filename: Path | str,
        file_open_kwargs: dict = {},
        **kwargs,
    ) -> Molecule:
        filename = Path(filename)
        with filename.open("r", **file_open_kwargs) as file:
            lines = file.read()
        return cls.get_toolkit_from_str(lines, **kwargs)

    @staticmethod
    def to_str_from_toolkit(molecule: Molecule):
        xyz = MolToXYZBlock(molecule.rdkit_molecule)
        if not xyz:
            raise Exception(
                "An empty string was given by the XyzAdapter. This happens if "
                "your molecule is not 3D. Use `convert_to_3d` before exporting."
            )
        return xyz

    @classmethod
    def to_file_from_toolkit(
        cls,
        molecule: Molecule,
        filename: Path | str,
        **kwargs,
    ):
        filename = Path(filename)

        with filename.open("w") as file:
            xyz_str = cls.to_str_from_toolkit(molecule, **kwargs)
            file.write(xyz_str)
