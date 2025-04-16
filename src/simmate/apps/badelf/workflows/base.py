# -*- coding: utf-8 -*-

import os
import shutil

# This will be added back once I go through and handle warnings within context
# import warnings
from pathlib import Path
from typing import Literal

from simmate.apps.badelf.core.badelf import SpinBadElfToolkit
from simmate.engine import Workflow
from simmate.toolkit import Structure

# This file contains workflows for performing Bader and BadELF. Parts of the code
# use the Henkelman groups algorithm for Bader analysis:
# (http://theory.cm.utexas.edu/henkelman/code/bader/).


class BadElfBase(Workflow):
    """
    Controls a Badelf analysis on a pre-ran VASP calculation.
    This is the base workflow that all analyses that run BadELF
    are built from. Note that for more in depth analysis, it may be more
    useful to use the BadElfToolkit class.
    """

    use_database = False

    @classmethod
    def run_config(
        cls,
        source: dict = None,
        directory: Path = None,
        find_electrides: bool = True,
        labeled_structure_up=None,
        labeled_structure_down=None,
        separate_spin=True,
        algorithm: Literal["badelf", "voronelf", "zero-flux"] = "badelf",
        shared_feature_algorithm: Literal["zero-flux", "voronoi"] = "zero-flux",
        shared_feature_separation_method: Literal[
            "plane", "pauling", "equal"
        ] = "pauling",
        elf_analyzer_kwargs: dict = dict(
            resolution=0.02,
            include_lone_pairs=False,
            include_shared_features=True,
            metal_depth_cutoff=0.1,
            min_covalent_angle=135,
            min_covalent_bond_ratio=0.4,
            shell_depth=0.05,
            electride_elf_min=0.5,
            electride_depth_min=0.2,
            electride_charge_min=0.5,
            electride_volume_min=10,
            electride_radius_min=0.3,
            radius_refine_method="linear",
        ),
        threads: int = None,
        ignore_low_pseudopotentials: bool = False,
        write_electride_files: bool = False,
        write_ion_radii: bool = True,
        write_labeled_structures: bool = True,
        run_id: str = None,
        **kwargs,
    ):
        # get cleaned labeled structures
        if labeled_structure_up is not None:
            labeled_structure_up = Structure.from_dynamic(labeled_structure_up)
        if labeled_structure_down is not None:
            labeled_structure_down = Structure.from_dynamic(labeled_structure_down)
        # make a new directory to run badelf algorithm in and copy necessary files.
        badelf_directory = directory / "badelf"
        try:
            os.mkdir(badelf_directory)
        except:
            pass
        files_to_copy = ["CHGCAR", "ELFCAR", "POTCAR"]
        for file in files_to_copy:
            shutil.copy(directory / file, badelf_directory)

        # Get the badelf toolkit object for running badelf.
        badelf_tools = SpinBadElfToolkit.from_files(
            directory=badelf_directory,
            find_electrides=find_electrides,
            algorithm=algorithm,
            separate_spin=separate_spin,
            labeled_structure_up=labeled_structure_up,
            labeled_structure_down=labeled_structure_down,
            threads=threads,
            shared_feature_algorithm=shared_feature_algorithm,
            ignore_low_pseudopotentials=ignore_low_pseudopotentials,
            elf_analyzer_kwargs=elf_analyzer_kwargs,
        )
        # run badelf.
        results = badelf_tools.results
        # write results
        if write_electride_files:
            badelf_tools.write_species_file()
            badelf_tools.write_species_file(file_type="CHGCAR")
        # grab the calculation table linked to this workflow run and save ionic
        # radii
        search_datatable = cls.database_table.objects.get(run_id=run_id)
        search_datatable.update_ionic_radii(badelf_tools.all_atom_elf_radii)
        # write ionic radii
        if write_ion_radii:
            badelf_tools.write_atom_elf_radii()
        if write_labeled_structures:
            badelf_tools.write_labeled_structures()
        badelf_tools.write_results_csv()
        return results
