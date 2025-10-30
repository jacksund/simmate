# -*- coding: utf-8 -*-
import os
from pathlib import Path

from baderkit.core import SpinElfLabeler
from baderkit.core.labelers.bifurcation_graph.enum_and_styling import FeatureType

from simmate.database import connect

from simmate.workflows.base_flow_types import Workflow
from simmate.apps.baderkit.models import SpinElfAnalysisCalculation


class SpinElfAnalysisCalculation__Baderkit__SpinElfAnalysis(Workflow):
    """
    Labels chemical features in the ELF and calculates various properties.
    Assumes the system is spin separated.
    """

    required_files = ["CHGCAR", "ELFCAR", "POTCAR"]
    use_database = True
    database_table = SpinElfAnalysisCalculation
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
        labeler = SpinElfLabeler.from_vasp(
            charge_filename=directory / "CHGCAR",
            reference_filename=directory / "ELFCAR",
            **kwargs
        )
        # update the database
        search_datatable = cls.database_table.objects.get(run_id=run_id)
        search_datatable.update_from_spin_labeler(
            labeler=labeler,
            directory=directory,
            **kwargs
            )
        # remove the ELFCAR, CHGCAR, and POTCAR copies for space
        for file in cls.use_previous_directory:
            os.remove(directory / file)
            
        # write summary plot, structures, etc.
        if write_files:
            labeler.write_bifurcation_plots(
                filename = directory / "bifurcation_plot.html"
                )
            labeler.labeled_structure.to(directory/"POSCAR_labeled", "POSCAR")
            labeler.quasi_atom_structure.to(directory/"POSCAR_quasi", "POSCAR")
            # write quasi atom volumes
            included = FeatureType.bare_types
            labeler.elf_labeler_up.write_features_by_type_sum(
                included_types=included,
                directory = directory,
                prefix_override = "ELFCAR_up"
                )
            labeler.elf_labeler_down.write_features_by_type_sum(
                included_types=included,
                directory = directory,
                prefix_override = "ELFCAR_down"
                )





