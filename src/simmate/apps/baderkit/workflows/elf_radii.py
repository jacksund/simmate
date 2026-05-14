# -*- coding: utf-8 -*-

from baderkit.elf_analysis import ElfRadii
from simmate.apps.baderkit.workflows.base import BaderkitVaspBase


class Baderkit__Baderkit__ElfRadii(BaderkitVaspBase):
    """
    Runs a ElfRadii analysis without running a static
    energy calculation. The directory must already have an
    ELFCAR and CHGCAR with the same grid size as well as the AECCAR0 and
    AECCAR2 files.

    This method assumes the calculation was NOT spin dependent.
    """

    required_files = ["AECCAR0", "AECCAR2", "CHGCAR", "ELFCAR", "POTCAR"]
    use_previous_directory = ["AECCAR0", "AECCAR2", "CHGCAR", "ELFCAR", "POTCAR"]
    charge_filename = "CHGCAR"
    reference_filename = "ELFCAR"
    baderkit_class = ElfRadii
    baderkit_kwargs = dict(
        cnn_kwargs = {}
        ) # Use CrystalNN instead of voronoi search

            