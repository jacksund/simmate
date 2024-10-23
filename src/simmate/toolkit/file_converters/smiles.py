# -*- coding: utf-8 -*-

from pathlib import Path

from rdkit.Chem import AllChem
from rich.progress import track

from simmate.toolkit import Molecule


class SmilesAdapter:
    @staticmethod
    def get_toolkit_from_smiles_str(smiles: str) -> Molecule:
        # this is the code for Molecule.from_smiles() method
        smiles = Molecule._clean_benchtop_conventions(smiles)
        rdkit_molecule = Molecule._load_rdkit(
            rdkit_loader=AllChem.MolFromSmiles,
            molecule_input=smiles,
        )
        return Molecule(rdkit_molecule)

    @staticmethod
    def get_toolkits_from_smiles_strs(smiless: list[str]) -> list[Molecule]:
        return [SmilesAdapter.get_toolkit_from_smiles_str(s) for s in smiless]

    @staticmethod
    def get_toolkits_from_smiles_file(filename: Path | str) -> list[Molecule]:
        # OPTMIZE: pandas could also be used to read SMI files
        # data = pandas.read_csv(
        #     file,
        #     delimiter="\t",
        #     header=None,
        #     names=["smiles", "id"],  # headers may vary
        # )
        filename = Path(filename)
        with filename.open("r") as file:
            lines = file.readlines()
        lines = [line.strip() for line in lines if line]  # cleans empties
        molecules = SmilesAdapter.get_toolkits_from_smiles_strs(lines)
        return molecules if len(molecules) > 1 else molecules[0]

    @staticmethod
    def to_file_from_toolkits(
        molecules: list[Molecule],
        filename: Path | str,
        **kwargs,
    ):
        filename = Path(filename)

        with filename.open("w") as file:
            for molecule in track(molecules):
                smi_str = molecule.to_smiles(**kwargs)
                file.write(f"{smi_str}\n")

    @staticmethod
    def split_smi_file(
        filename: Path | str,
        chunk_size: int,
        has_headers: bool = False,
    ):
        # !!! this is a copy/pase of the split_sdf_method. Consider making a
        # utility

        # OPTIMIZE:
        # This function SKIPS loading the sdf file into molecule objects
        # in order to make this a faster function.

        # doing a local import bc of the kemistree package
        from simmate.utilities import chunk_read

        filename = Path(filename)
        file_ext = filename.suffix
        file_header = None  # defined below if needed

        chunk_filenames = []
        for i, chunk in enumerate(
            chunk_read(
                filename=filename,
                chunk_size=chunk_size,
                delimiter="\n",
            )
        ):
            # if this is our first chunk AND we have headers, then we want to pull
            # these from the first line of the file
            if i == 0 and has_headers:
                file_header = chunk.pop(0)

            # separately (and for all chunks) we readd the header if there's one
            if file_header:
                chunk.insert(0, file_header)

            chunk_filename = Path(f"{filename.stem}_{str(i).zfill(3)}{file_ext}")
            with chunk_filename.open("w") as file:
                file.write("\n".join(chunk))
            chunk_filenames.append(chunk_filename)

        return chunk_filenames
