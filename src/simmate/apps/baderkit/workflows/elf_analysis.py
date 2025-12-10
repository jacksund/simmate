# -*- coding: utf-8 -*-
import os
from pathlib import Path

from baderkit.core import ElfLabeler
from baderkit.core.labelers.bifurcation_graph.enum_and_styling import FeatureType

from simmate.database import connect

from simmate.workflows.base_flow_types import Workflow
from simmate.apps.baderkit.models import ElfAnalysisCalculation


class ElfAnalysisCalculation__Baderkit__ElfAnalysis(Workflow):
    """
    Labels chemical features in the ELF and calculates various properties.
    Assumes the system is not spin separated.
    """

    required_files = ["CHGCAR", "ELFCAR", "POTCAR"]
    use_database = True
    database_table = ElfAnalysisCalculation
    use_previous_directory = ["CHGCAR", "ELFCAR", "POTCAR"]

    @classmethod
    def run_config(
        cls,
        source: dict = None,
        directory: Path = None,
        write_files: bool = True,
        run_id = None,
        **kwargs,
    ):

        # Get the badelf toolkit object for running badelf.
        labeler = ElfLabeler.from_vasp(
            charge_filename=directory / "CHGCAR",
            reference_filename=directory / "ELFCAR",
            **kwargs
        )
        # update the database
        analysis_datatable = cls.database_table.objects.get(run_id=run_id)
        analysis_datatable.update_from_labeler(
            labeler=labeler,
            directory=directory,
            **kwargs
            )
        # remove the ELFCAR, CHGCAR, and POTCAR copies for space
        for file in cls.use_previous_directory:
            os.remove(directory / file)
            
        # write summary plot, structures, etc.
        if write_files:
            labeler.write_bifurcation_plot(
                filename = directory / "bifurcation_plot.html"
                )
            labeler.labeled_structure.to(directory/"POSCAR_labeled", "POSCAR")
            labeler.electride_structure.to(directory/"POSCAR_quasi", "POSCAR")
            # write quasi atom volume
            included = FeatureType.bare_types
            labeler.write_features_by_type_sum(
                included_types=included,
                directory = directory
                )





