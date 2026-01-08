# -*- coding: utf-8 -*-

from pathlib import Path

from baderkit.core import SpinElfLabeler

from simmate.database.base_data_types import (
    Calculation,
    table_column,
)

from .elf_analysis import ElfAnalysis


class SpinElfAnalysis(ElfAnalysis):
    """
    This table contains results from a spin-dependant ELF topology analysis
    calculation. It intentionally does not inherit from the Calculation
    table as the results may not be calculated from a dedicated workflow.
    """

    class Meta:
        app_label = "baderkit"

    analysis_up = table_column.ForeignKey(
        "baderkit.ElfAnalysis",
        on_delete=table_column.CASCADE,
        related_name="spin_analysis",
        blank=True,
        null=True,
    )

    analysis_down = table_column.ForeignKey(
        "baderkit.ElfAnalysis",
        on_delete=table_column.CASCADE,
        related_name="spin_analysis",
        blank=True,
        null=True,
    )

    differing_spin = table_column.BooleanField(blank=True, null=True)
    """
    Whether the spin up and spin down differ in the ELF and charge density
    """

    def update_from_directory(self, directory):
        """
        The base database workflow will try and register data from the local
        directory. As part of this it checks for a vasprun.xml file and
        attempts to run a from_vasp_run method. Since this is not defined for
        this model, an error is thrown. To account for this, I just create an empty
        update_from_directory method here.
        """
        pass

    @classmethod
    def from_labeler(cls, labeler: SpinElfLabeler, directory: Path, **kwargs):
        """
        Creates a new row from a SpinElfLabeler object
        """
        # get initial row from ElfLabeler method
        new_row = super().from_labeler(labeler, directory)

        # create spin up/down entries
        labeler_up = ElfAnalysis.from_labeler(labeler.elf_labeler_up, directory)
        labeler_down = ElfAnalysis.from_labeler(labeler.elf_labeler_down, directory)

        # update entry
        new_row.analysis_up = labeler_up
        new_row.analysis_down = labeler_down
        new_row.differing_spin = not labeler.equal_spin
        new_row.save()
        return new_row


class SpinElfAnalysisCalculation(Calculation):
    """
    This table contains results from a spin-separated ELF topology
    analysis calculation. The results should be from a dedicated workflow.
    """

    class Meta:
        app_label = "baderkit"

    analysis = table_column.ForeignKey(
        "baderkit.SpinElfAnalysis",
        on_delete=table_column.CASCADE,
        related_name="calculation",
        blank=True,
        null=True,
    )

    def update_from_labeler(self, labeler: SpinElfLabeler, directory: Path, **kwargs):
        # create an entry in the SpinElfAnalysis table
        labeler = SpinElfAnalysis.from_labeler(labeler, directory)
        # link to table
        self.analysis = labeler
        self.save()
