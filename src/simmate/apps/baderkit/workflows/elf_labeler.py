# -*- coding: utf-8 -*-

from baderkit.elf_analysis import ElfLabeler
from simmate.apps.baderkit.workflows.base import BaderkitVaspBase, BaderkitVaspSpinBase


class Baderkit__Baderkit__ElfLabeler(BaderkitVaspBase):
    """
    Runs a ElfLabeler analysis without running a static
    energy calculation. The directory must already have an
    ELFCAR and CHGCAR with the same grid size as well as the AECCAR0 and
    AECCAR2 files.

    This method assumes the calculation was NOT spin dependent.
    """

    required_files = ["AECCAR0", "AECCAR2", "CHGCAR", "ELFCAR", "POTCAR"]
    use_previous_directory = ["AECCAR0", "AECCAR2", "CHGCAR", "ELFCAR", "POTCAR"]
    charge_filename = "CHGCAR"
    reference_filename = "ELFCAR"
    baderkit_class = ElfLabeler

            
class Baderkit__Baderkit__SpinElfLabeler(BaderkitVaspSpinBase):
    """
    Runs a ElfLabeler analysis without running a static
    energy calculation. The directory must already have an
    ELFCAR and CHGCAR with the same grid size as well as the AECCAR0 and
    AECCAR2 files.

    This method assumes the calculation WAS spin dependent.
    """

    required_files = ["AECCAR0", "AECCAR2", "CHGCAR", "ELFCAR", "POTCAR"]
    use_previous_directory = ["AECCAR0", "AECCAR2", "CHGCAR", "ELFCAR", "POTCAR"]
    charge_filename = "CHGCAR"
    reference_filename = "ELFCAR"
    baderkit_class = ElfLabeler