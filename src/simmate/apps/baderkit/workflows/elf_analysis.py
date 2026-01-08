# -*- coding: utf-8 -*-
import os
from pathlib import Path

from baderkit.core import ElfLabeler, SpinElfLabeler
from baderkit.core.labelers.bifurcation_graph.enum_and_styling import FeatureType

from simmate.apps.baderkit.models import (
    ElfAnalysisCalculation,
    SpinElfAnalysisCalculation,
)
from simmate.database import connect
from simmate.workflows.base_flow_types import Workflow


class ElfAnalysisBase(Workflow):
    """
    The base class for running the ElfLabeler from baderkit. This should
    not be run directly, but inherited from.

    """

    labeler_class = None
    required_files = ["CHGCAR", "ELFCAR", "POTCAR"]
    use_database = False
    use_previous_directory = ["CHGCAR", "ELFCAR", "POTCAR"]

    @classmethod
    def run_config(
        cls,
        source: dict = None,
        directory: Path = None,
        run_id=None,
        **kwargs,
    ):

        # Get the badelf toolkit object for running badelf.
        labeler = cls.labeler_class.from_vasp(
            charge_filename=directory / "CHGCAR",
            reference_filename=directory / "ELFCAR",
            **kwargs,
        )
        # update the database
        analysis_datatable = cls.database_table.objects.get(run_id=run_id)
        analysis_datatable.update_from_labeler(
            labeler=labeler, directory=directory, **kwargs
        )

        # write summary plot, structures, etc.
        labeler.write_bifurcation_plot(filename=directory / "bifurcation_plot.html")
        labeler.labeled_structure.to(directory / "POSCAR_labeled", "POSCAR")
        labeler.electride_structure.to(directory / "POSCAR_e", "POSCAR")
        labeler.write_json(directory / "labeler.json", potcar_path=directory / "POTCAR")
        # write quasi atom volume
        labeler.write_features_by_type(
            included_types=[FeatureType.electride], directory=directory
        )

        # remove the ELFCAR, CHGCAR, and POTCAR copies for space
        for file in cls.use_previous_directory:
            os.remove(directory / file)


class ElfAnalysis__Baderkit__ElfAnalysis(ElfAnalysisBase):
    """
    Labels chemical features in the ELF and calculates various properties.
    Assumes the system is not spin separated.
    """

    use_database = True
    database_table = ElfAnalysisCalculation
    labeler_class = ElfLabeler


class ElfAnalysis__Baderkit__SpinElfAnalysis(ElfAnalysisBase):
    """
    Labels chemical features in the ELF and calculates various properties.
    Assumes the system is spin separated.
    """

    use_database = True
    database_table = SpinElfAnalysisCalculation
    labeler_class = SpinElfLabeler
