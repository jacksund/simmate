# -*- coding: utf-8 -*-

import os
import shutil

# This will be added back once I go through and handle warnings within context
# import warnings
from pathlib import Path

from simmate.apps.badelf.core.badelf import BadElfToolkit
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
        cores: int = None,
        find_electrides: bool = True,
        electride_finder_cutoff: float = 0.5,  # This is somewhat arbitrarily set
        algorithm: str = "badelf",
        electride_connection_cutoff: float = 0,
        check_for_covalency: bool = True,
        **kwargs,
    ):
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
        badelf_tools = BadElfToolkit.from_files(
            directory=badelf_directory,
            find_electrides=find_electrides,
            algorithm=algorithm,
        )
        # Set options and run badelf.
        if not check_for_covalency:
            badelf_tools.check_for_covalency = False
        badelf_tools.electride_finder_cutoff = electride_finder_cutoff
        badelf_tools.electride_connection_cutoff = electride_connection_cutoff
        results = badelf_tools.results
        badelf_tools.write_results_csv()
        return results


class VaspBadElfBase(Workflow):
    """
    Runs a VASP DFT calculation followed by a BadELF analysis. This is the base
    workflow that all analyses that run DFT and BadELF are built from.
    """

    use_database = False
    static_energy_workflow = None  # This should be defined in the inheriting class
    badelf_workflow = None  # This should be defined in the inheriting class
    # usually as the BadElfAnalyisis__WarrenLab__badelf workflow

    @classmethod
    def run_config(
        cls,
        structure: Structure,
        command: str = None,
        source: dict = None,
        directory: Path = None,  # we default to the current directory
        cores: int = None,
        find_electrides: bool = True,
        electride_finder_cutoff: float = 0.5,  # This is somewhat arbitrarily set
        algorithm: str = "badelf",
        electride_connection_cutoff: float = 0,
        check_for_covalency: bool = True,
        **kwargs,
    ):
        # Run the dft calculation. This workflow should be set as something
        # that already saves to a database table.
        static_energy_directory = directory / "static_energy"
        static_energy_result = cls.static_energy_workflow.run(
            structure=structure,
            command=command,
            source=source,
            directory=static_energy_directory,
        ).result()

        # run the badelf analysis in the same directory as the DFT. This workflow
        # should be set to something that already saves to a database table.

        badelf_result = cls.badelf_workflow.run(
            source=source,
            directory=static_energy_directory,
            cores=cores,
            find_electrides=find_electrides,
            electride_finder_cutoff=electride_finder_cutoff,
            algorithm=algorithm,
            electride_connection_cutoff=electride_connection_cutoff,
            check_for_covalency=check_for_covalency,
            # copy_previous_directory=True,
        ).result()
