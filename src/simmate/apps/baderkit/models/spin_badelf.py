# -*- coding: utf-8 -*-

from pathlib import Path

from baderkit.core import SpinBadelf as SpinBadelfClass

from simmate.apps.baderkit.models.spin_elf_analysis import SpinElfAnalysis
from simmate.database.base_data_types import (
    Calculation,
    table_column,
)

from .badelf import Badelf


class SpinBadelf(Badelf):
    """
    Contains results from a spin-separated BadELF analysis.
    It intentionally does not inherit from the Calculation
    table as the results may not be calculated from a dedicated workflow.
    """

    _analysis_model = SpinElfAnalysis

    class Meta:
        app_label = "baderkit"

    badelf_up = table_column.ForeignKey(
        "baderkit.Badelf",
        on_delete=table_column.CASCADE,
        related_name="spin_badelf",
        blank=True,
        null=True,
    )

    badelf_down = table_column.ForeignKey(
        "baderkit.Badelf",
        on_delete=table_column.CASCADE,
        related_name="spin_badelf",
        blank=True,
        null=True,
    )

    # elf_analysis = table_column.ForeignKey(
    #     "baderkit.SpinElfAnalysis",
    #     on_delete=table_column.CASCADE,
    #     related_name="badelf",
    #     blank=True,
    #     null=True,
    # )
    """
    The SpinElfAnalysis table entry from this calculation which includes
    more detailed information on each chemical feature found in the
    system.
    """

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
    def from_badelf(cls, badelf: SpinBadelfClass, directory: Path, **kwargs):
        """
        Creates a new row from a SpinElfLabeler object
        """
        # get initial row from ElfLabeler method
        new_row = super().from_badelf(badelf, directory)

        # create spin up/down entries
        badelf_up = Badelf.from_badelf(badelf.badelf_up, directory)
        badelf_down = Badelf.from_badelf(badelf.badelf_down, directory)

        # connect labelers
        badelf_up.elf_analysis = new_row.elf_analysis.analysis_up
        badelf_down.elf_analysis = new_row.elf_analysis.analysis_down
        badelf_up.save()
        badelf_down.save()

        # update entry
        new_row.badelf_up = badelf_up
        new_row.badelf_down = badelf_down
        new_row.differing_spin = not badelf.equal_spin
        new_row.save()
        return new_row


class SpinBadelfCalculation(Calculation):
    """
    This table contains results from a spin-separated ELF topology
    analysis calculation. The results should be from a dedicated workflow.
    """

    class Meta:
        app_label = "baderkit"

    badelf = table_column.ForeignKey(
        "baderkit.SpinBadElf",
        on_delete=table_column.CASCADE,
        related_name="calculation",
        blank=True,
        null=True,
    )

    def update_from_badelf(self, badelf: SpinBadelfClass, directory: Path, **kwargs):
        # create an entry in the SpinBadelf table
        badelf_entry = SpinBadelf.from_badelf(badelf, directory)
        # link to table
        self.badelf = badelf_entry
        self.save()
