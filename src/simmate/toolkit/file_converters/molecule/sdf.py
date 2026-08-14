# -*- coding: utf-8 -*-

import logging
import re
from pathlib import Path

from rdkit.Chem import AllChem
from rich.progress import track

from simmate.toolkit import Molecule


class SdfAdapter:

    # Property tags are written as `>  <My Key>` but the number of spaces
    # varies between programs (e.g. ChemDraw uses two, others use one)
    property_key_pattern = re.compile(r"^>\s*<(.+?)>")

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
            metadata = SdfAdapter.get_metadata_from_sdf_str(sdf)
            for key, value in metadata.items():
                rdkit_molecule.SetProp(key, value)

        return Molecule(rdkit_molecule)

    @staticmethod
    def get_metadata_from_sdf_str(sdf: str) -> dict:
        """
        Grabs the property block (i.e. the metadata) out of a single SDF record.

        Note, we scan the record line-by-line rather than splitting the string
        on the molfile terminator. Property *values* often contain the substring
        "END" (e.g. company names such as "Ascend Performance Materials"), which
        would otherwise silently throw away every property before it.
        """
        metadata = {}
        key = None
        values = []
        in_properties = False

        for line in sdf.split("\n"):
            # everything before the molfile terminator is the structure
            if not in_properties:
                if line.strip() == "M  END":
                    in_properties = True
                continue

            key_match = SdfAdapter.property_key_pattern.match(line)
            if key_match:
                if key:
                    metadata[key] = "\n".join(values).strip()
                key = key_match.group(1)
                values = []
            elif key is not None:
                # values can span several lines
                values.append(line)

        if key:
            metadata[key] = "\n".join(values).strip()

        # rdkit doesn't let us set an empty value, so we drop those keys
        return {k: v for k, v in metadata.items() if v}

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
        for record_number, sdf_str in enumerate(lines.split("$$$$"), start=1):
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
                    logging.warning(
                        f"Failed to load SDF record {record_number} "
                        f"of {filename.name}: {error}"
                    )
                    continue
                else:
                    raise error
            molecules.append(molecule)

        return molecules if len(molecules) > 1 else molecules[0]

    @staticmethod
    def to_str_from_toolkits(
        molecules: list[Molecule],
        **kwargs,
    ):
        final_str = ""
        for molecule in track(molecules):
            mol_str = molecule.to_sdf(**kwargs)
            final_str += mol_str
        return final_str

    @classmethod
    def to_file_from_toolkits(
        cls,
        molecules: list[Molecule],
        filename: Path | str,
        **kwargs,
    ):
        filename = Path(filename)

        with filename.open("w") as file:
            # NOTE: we do not use `to_str_from_toolkits` in case there are many
            # molecules -- this saves on memory
            for molecule in track(molecules):
                smi_str = molecule.to_sdf(**kwargs)
                file.write(f"{smi_str}")

    @staticmethod
    def split_sdf_file(filename: Path | str, chunk_size: int) -> list[Path]:
        # OPTIMIZE:
        # This function SKIPS loading the sdf file into molecule objects
        # in order to make this a faster function.

        # doing a local import bc of the kemistree package
        from simmate.utils import chunk_read

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
