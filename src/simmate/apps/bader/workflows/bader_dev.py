# -*- coding: utf-8 -*-

from pathlib import Path

from simmate.engine import S3Workflow
from simmate.toolkit import Structure


class PopulationAnalysis__Bader__BaderDev(S3Workflow):
    use_database = False
    parent_workflows = ["population-analysis.vasp-bader.bader-matproj"]
    command = "bader {charge_file}"

    @classmethod
    def get_final_command(
        cls,
        charge_file: Path | str = "CHGCAR",
        partitioning_file: Path | str = None,
        atoms_to_print: list[int] = [],
        species_to_print: str = [],
        structure: Structure = None,
        **kwargs,
    ) -> str:
        """
        Builds the command to call bader

        Args:
            charge_file (str): The name of the file containing charge density
                data.

            partitioning_file (str): The name of the file to use for partitioning.

            atoms_to_print (list):
                A list of atom indices to print. Should be
                indices starting at 0.

            species_to_print : list
                The symbol of the atom type to print.

            structure : Structure
                The pymatgen structure object for the system of interest.
        """

        # start with the minimal required command
        command_final = cls.command.format(
            charge_file=charge_file,
            partitioning_file=partitioning_file,
        )

        # Now go through the extra optional kwargs bader cli
        if partitioning_file:
            command_final += f" -ref {partitioning_file}"

        if atoms_to_print and species_to_print:
            raise Exception(
                "Set either `atoms_to_print` or `species_to_print`. "
                "You cannot set both"
            )
        elif atoms_to_print:
            indices_str = " ".join([str(i + 1) for i in atoms_to_print])
            command_final += f" -p sel_atom {indices_str}"
        elif species_to_print:
            if not structure:
                raise Exception(
                    "You must provide a struture when setting `species_to_print`"
                )
                # TODO: grab the structure from the CHGCAR
            atom_indices = structure.indices_from_symbol(species_to_print)
            indices_str = indices_str = " ".join([str(i + 1) for i in atom_indices])
            command_final += f" -p sum_atom {indices_str}"
        return command_final
