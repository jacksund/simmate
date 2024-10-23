# -*- coding: utf-8 -*-

from pathlib import Path

from rdkit.Chem import AllChem
from rich.progress import track

from simmate.toolkit import Molecule


class SdfAdapter:
    @staticmethod
    def get_toolkit_from_sdf_str(
        sdf: str,
        remove_hs: bool = True,
        strict_parsing: bool = True,
        read_metadata: bool = True,
    ) -> Molecule:
        # this is the code for Molecule.from_sdf() method

        rdkit_molecule = Molecule._load_rdkit(
            rdkit_loader=AllChem.MolFromMolBlock,
            molecule_input=sdf,
            removeHs=remove_hs,
            strictParsing=strict_parsing,
        )

        # workup metadata
        if read_metadata:
            metadata_lines = sdf.split("END")[-1].strip().split("\n\n")
            for line in metadata_lines:
                if not line:
                    continue
                line_objs = line.split("\n")
                # Check for bug where there's a key but no value given
                if len(line_objs) == 2:
                    key, value = line_objs
                # rdkit doesn't let us set key=None, so we skip it
                else:
                    continue
                # clean key format
                key = key[4:-1]
                # then add to rdkit mol
                rdkit_molecule.SetProp(key, value)

        return Molecule(rdkit_molecule)

    @staticmethod
    def get_toolkits_from_sdf_strs(sdfs: list[str]) -> list[Molecule]:
        return [SdfAdapter.get_toolkit_from_sdf_str(s) for s in sdfs]

    @staticmethod
    def get_toolkits_from_sdf_file(
        filename: Path | str,
        skip_failed: bool = False,
        file_open_kwargs: dict = {},
        **kwargs,
    ) -> list[Molecule]:
        # OPTIMIZE:
        # AllChem.SDMolSupplier is wacky... so I opted to do manual loading instead

        filename = Path(filename)
        with filename.open("r", **file_open_kwargs) as file:
            lines = file.read()

        molecules = []
        for sdf_str in lines.split("$$$$"):
            # make sure we don't have an empty string
            sdf_str = sdf_str.strip()
            if not sdf_str:
                continue

            # the before/end lines vary in sdf files, so we strip all lines (above)
            # and then add one at the start/end manually. We only need to add
            # a new line at the start IF there isnt a name set
            sdf_str += "\n"  # end of string
            if not sdf_str.split("\n")[1]:
                sdf_str = "\n" + sdf_str  # start of string
            # catch errors
            try:
                molecule = Molecule.from_sdf(sdf_str, **kwargs)
            except Exception as error:
                if skip_failed:
                    continue
                else:
                    raise error
            molecules.append(molecule)

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
                smi_str = molecule.to_sdf(**kwargs)
                file.write(f"{smi_str}$$$$\n")

    @staticmethod
    def split_sdf_file(filename: Path | str, chunk_size: int) -> list[Path]:
        # OPTIMIZE:
        # This function SKIPS loading the sdf file into molecule objects
        # in order to make this a faster function.

        # doing a local import bc of the kemistree package
        from simmate.utilities import chunk_read

        filename = Path(filename)
        chunk_filenames = []
        for i, chunk in enumerate(
            chunk_read(
                filename=filename,
                chunk_size=chunk_size,
                delimiter="$$$$",
            )
        ):
            chunk_filename = Path(f"{filename.stem}_{str(i).zfill(3)}.sdf")
            with chunk_filename.open("w") as file:
                file.write("$$$$".join(chunk))
            chunk_filenames.append(chunk_filename)

        return chunk_filenames
