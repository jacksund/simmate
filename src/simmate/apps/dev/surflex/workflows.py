# -*- coding: utf-8 -*-

"""
Official surflex docs: https://www.biopharmics.com/Public/Surflex-Manual.pdf

source files for surflex (SF-Full-Distribution-v5142.tar.gz) were grabbed
from /share/apps/surflex/5.142

# to use...
module load surflex

# make sure license file is present...
/share/apps/surflex/5.142/bin/surflex_api.lic
"""

import shutil
from pathlib import Path

from simmate.engine import Workflow
from simmate.workflows.base_flow_types import S3Workflow
from simmate.toolkit import Molecule
from simmate.toolkit.file_converters import SmilesAdapter

__all__ = [
    "ConformerGeneration__Surflex__Fgen3d",
    "ConformerGeneration__Surflex__ForceGen",
    "ConformerGeneration__Surflex__FullGen",
    "Similarity__Surflex__ESimList",
    "PrototypeGen__Surflex__DockProto",
    "Docking__Surflex__DockList",
    "Docking__Surflex__FullFlow",
]

# -----------------------------------------------------------------------------

# STEP 1: Generate conformers. This involves two separate commands that we
# then combine together in a bigger workflow


class ConformerGeneration__Surflex__Fgen3d(S3Workflow):
    required_files = ["input_molecules.smi"]
    monitor = False
    use_database = False
    command = "sf-tools.exe fgen3d input_molecules.smi output"

    @staticmethod
    def setup(
        molecules: list[Molecule],
        directory: Path,
        **kwargs,
    ):
        # Write all molecules to an input file.
        # For now, we assume that the Molecules are 2D and can be
        # written to SMILES. But in the future, we might want to consider 3D
        # which can speed up conformer relaxation
        input_filename = directory / "input_molecules.smi"
        SmilesAdapter.to_file_from_toolkits(molecules, input_filename)


class ConformerGeneration__Surflex__ForceGen(S3Workflow):
    """
    Force Field Based Conformational Generation (ForceGen)

    3D structure generation and enumeration of stereocenters

    https://link.springer.com/article/10.1007/s10822-017-0015-8
    """

    required_files = ["input_molecules.mol2"]
    monitor = False
    use_database = False
    command = "sf-tools.exe -pscreen forcegen input_molecules.mol2 output"

    @staticmethod
    def setup(
        mol2_file: str,  # should be "molecule"
        directory: Path,
        **kwargs,
    ):
        # BUG: rdkit can't parse or write mol2 files so this workflow has
        # limited input options... For now we just copy/paste over the input
        input_filename = directory / "input_molecules.mol2"
        shutil.copyfile(src=mol2_file, dst=input_filename)
        # TODO: use the 'ext_sfdb_sdf' command to convert so that we can read
        # these molecules back into simmate


class ConformerGeneration__Surflex__FullGen(Workflow):
    use_database = False

    @staticmethod
    def run_config(
        molecules: list[Molecule],
        directory: Path,
        **kwargs,
    ):
        ConformerGeneration__Surflex__Fgen3d.run(
            directory=directory / ConformerGeneration__Surflex__Fgen3d.name_full,
            molecules=molecules,
        )

        ConformerGeneration__Surflex__ForceGen.run(
            directory=directory / ConformerGeneration__Surflex__ForceGen.name_full,
            mol2_file=directory
            / ConformerGeneration__Surflex__Fgen3d.name_full
            / "output.mol2",
        )


# -----------------------------------------------------------------------------

# STEP 2: A 3D similarity search that filters a set of molecules down to those
# similar to a given "query" (or known "ligand")


class Similarity__Surflex__ESimList(S3Workflow):
    required_files = ["input_molecules.sfdb", "query_molecule.mol2"]
    monitor = False
    use_database = False
    command = (
        "sf-sim.exe -min_output 6.0 -pscreen -nfinal 1 esim_list "
        "input_molecules.sfdb query_molecule.mol2 output"
    )

    @staticmethod
    def setup(
        mol2_file: str,  # should be "molecule"
        sfdb_file: str,  # should be "molecules"
        directory: Path,
        **kwargs,
    ):
        # BUG: rdkit can't parse or write mol2/sfdb files so this workflow has
        # limited input options... For now we just copy/paste over the inputs

        # the molecule we want a 3D similarity on
        molecule_filename = directory / "query_molecule.mol2"
        shutil.copyfile(src=mol2_file, dst=molecule_filename)

        # The entire molecule library to compare it to
        library_filename = directory / "input_molecules.sfdb"
        shutil.copyfile(src=sfdb_file, dst=library_filename)


# -----------------------------------------------------------------------------

# STEP 3: Docking of the ligand to the protein. This generates the protomol
# and corevox that will be used for high-throughput docking in the next step


class PrototypeGen__Surflex__DockProto(S3Workflow):
    required_files = ["ligand.mol2", "protein.mol2"]
    monitor = False
    use_database = False
    command = "sf-dock.exe proto ligand.mol2 protein.mol2 output"
    # outputs --> output-corevox.mol2  output-protomol.mol2

    @staticmethod
    def setup(
        ligand_mol2_file: str,  # should be "molecule" or "ligand"
        protein_mol2_file: str,  # should be "protein"
        directory: Path,
        **kwargs,
    ):
        # BUG: rdkit can't parse or write mol2/sfdb files so this workflow has
        # limited input options... For now we just copy/paste over the inputs
        ligand_filename = directory / "ligand.mol2"
        shutil.copyfile(src=ligand_mol2_file, dst=ligand_filename)
        protein_filename = directory / "protein.mol2"
        shutil.copyfile(src=protein_mol2_file, dst=protein_filename)


# -----------------------------------------------------------------------------

# STEP 4: Docking many molecules to a protein


class Docking__Surflex__DockList(S3Workflow):
    required_files = [
        "ligand.mol2",  # from user
        "Protein.mol2",  # from user
        "protomol.mol2",  # from DockProto
        "corevox.mol2",  # from DockProto
        "input_molecules.sfdb",  # from ESimList
    ]
    monitor = False
    use_database = False
    command = (
        "sf-dock.exe -min_output 6.0 -pscreen dock_list "
        "input_molecules.sfdb protomol.mol2 corevox.mol2 Protein.mol2 output"
    )

    # @staticmethod
    # def setup(
    #     ligand_mol2_file: str,  # should be "molecule" or "ligand"
    #     protein_mol2_file: str,  # should be "protein"
    #     directory: Path,
    #     **kwargs,
    # ):
    #     # BUG: rdkit can't parse or write mol2/sfdb files so this workflow has
    #     # limited input options... For now we just copy/paste over the inputs
    #     ligand_filename = directory / "ligand.mol2"
    #     shutil.copyfile(src=ligand_mol2_file, dst=ligand_filename)
    #     protein_filename = directory / "protein.mol2"
    #     shutil.copyfile(src=protein_mol2_file, dst=protein_filename)


# -----------------------------------------------------------------------------

# STEP 5: Combines all workflows above into a single one.


class Docking__Surflex__FullFlow(S3Workflow):
    @staticmethod
    def _run_config(
        ligand: Molecule,
        protein: Molecule,
        # molecules: list[Molecule],  # assumed for now
        directorty: Path = None,
        **kwargs,
    ):
        ConformerGeneration__Surflex__Fgen3d.run(
            directory=directorty / "step00",
            molecules="ligand.smi",
        )
        ConformerGeneration__Surflex__Fgen3d.run(
            directory=directorty / "step01",
            molecules="input.smi",
        )

        ConformerGeneration__Surflex__ForceGen.run(
            directory=directorty / "step02",
            mol2_file="step01/output.mol2",
        )

        Similarity__Surflex__ESimList.run(
            directory=directorty / "step03",
            # mol2_file="step00/output.mol2",
            mol2_file="ligand.mol2",
            sfdb_file="step02/output.sfdb",
        )

        PrototypeGen__Surflex__DockProto.run(
            directory=directorty / "step04",
            ligand_mol2_file="ligand.mol2",
            protein_mol2_file="protein.mol2",
        )


# -----------------------------------------------------------------------------
