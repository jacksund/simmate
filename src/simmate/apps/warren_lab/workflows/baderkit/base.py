# -*- coding: utf-8 -*-

from pathlib import Path

from simmate.toolkit import Structure
from simmate.workflows import Workflow


class BaderkitStagedBase(Workflow):
    """
    The calculations using baderkit are always staged, starting with dft. This
    is a skeleton structure to make building out the rest of this process simple.
    """

    use_database = False  # nested workflows save separately
    
    workflows = []

    @classmethod
    def run_config(
        cls,
        structure: Structure,
        source: dict = None,
        directory: Path = None,
        subworkflow_kwargs: dict = {},
        **kwargs,
    ):
        # run the first workflow
        workflow = cls.workflows[0]
        current_dir = directory / workflow.name_full
        result = workflow.run(
            structure=structure,
                source=source,
                directory=current_dir,
                **subworkflow_kwargs,
            )
        previous_dir = current_dir
        
        for workflow in cls.workflows[1:]:
            previous_dir = current_dir
            current_dir = directory / workflow.name_full
            result = workflow.run(
                directory=current_dir,
                previous_directory=previous_dir,
                source=result,
                **subworkflow_kwargs,
            )

