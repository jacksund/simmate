# -*- coding: utf-8 -*-

from simmate.apps.badelf.models import BadElf
from simmate.apps.badelf.workflows.base import BadElfBase
from simmate.database import connect


class BadElf__Badelf__Badelf(BadElfBase):
    """
    This class runs a Bader and BadELF analysis without running a static
    energy calculation. The directory it is run in must already have an
    ELFCAR and CHGCAR with the same grid size as well as the AECCAR0 and
    AECCAR2 files.

    This workflow must be run with a specified directory that already exists!
    If you're using a settings.yaml file it should be in the directory above.
    You will also need to place a POSCAR file in the directory above.
    """

    use_database = True
    database_table = BadElf
