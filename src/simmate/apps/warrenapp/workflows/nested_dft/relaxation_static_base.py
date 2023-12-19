# -*- coding: utf-8 -*-

import os
import shutil
from pathlib import Path

from simmate.engine import Workflow
from simmate.toolkit import Structure


class RelaxationStaticBase(Workflow):
    """
    Base class for running a relaxation followed by a static energy
    calculation.

    This should NOT be run on its own. It is meant to be inherited from in
    other workflows.
    """

    # We don't want to save anything from the parent workflow, only the
    # sub workflows (relaxation and static energy) so we set use_database=False
    use_database = False
    relaxation_workflow = None  # This will be defined in inheriting workflows
    static_energy_workflow = None  # This will be defined in inheriting workflows

    @classmethod
    def run_config(
        cls,
        structure: Structure,
        command: str = None,
        source: dict = None,
        directory: Path = None,
        **kwargs,
    ):
        # run a relaxation
        relaxation_directory = directory / "relaxation"
        relaxation_result = cls.relaxation_workflow.run(
            structure=structure,
            command=command,
            source=source,
            directory=relaxation_directory,
        ).result()

        static_energy_directory = directory / "static_energy"
        # run a static energy and bader/badelf analysis using the same structure
        # as above.
        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        # We need to make a new directory because only one vasp workflow can
        # be run in each directory.
        os.mkdir(static_energy_directory)
        shutil.copyfile(
            relaxation_directory / "WAVECAR", static_energy_directory / "WAVECAR"
        )
        static_energy_result = cls.static_energy_workflow.run(
            structure=relaxation_result,
            command=command,
            source=source,
            directory=static_energy_directory,
            # copy_previous_directory=True,
        )


class RelaxationRelaxationStaticBase(Workflow):
    """
    Base class for running a PBE relaxation followed by an HSE relaxation
    and then a static energy calculation.

    This should NOT be run on its own. It is meant to be inherited from in
    other workflows.
    """

    # We don't want to save anything from the parent workflow, only the
    # sub workflows (relaxation and static energy) so we set use_database=False
    use_database = False
    low_quality_relaxation_workflow = (
        None  # This will be defined in inheriting workflows
    )
    high_quality_relaxation_workflow = (
        None  # This will be defined in inheriting workflows
    )
    static_energy_workflow = None  # This will be defined in inheriting workflows

    @classmethod
    def run_config(
        cls,
        structure: Structure,
        command: str = None,
        source: dict = None,
        directory: Path = None,
        **kwargs,
    ):
        # run a relaxation at low quality
        relaxation1_directory = directory / "low_quality_relaxation"
        relaxation1_result = cls.low_quality_relaxation_workflow.run(
            structure=structure,
            command=command,
            source=source,
            directory=relaxation1_directory,
        ).result()

        # make the directory for the second relaxation and copy the WAVECAR
        # then run
        relaxation2_directory = directory / "high_quality_relaxation"
        os.mkdir(relaxation2_directory)
        shutil.copyfile(
            relaxation1_directory / "WAVECAR", relaxation2_directory / "WAVECAR"
        )
        relaxation2_result = cls.high_quality_relaxation_workflow.run(
            structure=relaxation1_result,
            command=command,
            directory=relaxation2_directory,
            # copy_previous_directory=True
        ).result()

        static_energy_directory = directory / "static_energy"
        # run a static energy and bader/badelf analysis using the same structure
        # as above.
        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        # We need to make a new directory because only one vasp workflow can
        # be run in each directory.
        os.mkdir(static_energy_directory)
        shutil.copyfile(
            relaxation2_directory / "WAVECAR", static_energy_directory / "WAVECAR"
        )
        static_energy_result = cls.static_energy_workflow.run(
            structure=relaxation2_result,
            command=command,
            directory=static_energy_directory,
            # copy_previous_directory=True,
        )
