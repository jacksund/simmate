# -*- coding: utf-8 -*-

from baderkit import Bader

from simmate.apps.baderkit.workflows.base import BaderkitVaspBase


class Baderkit__Baderkit__Bader(BaderkitVaspBase):

    """
    Runs a Bader charge analysis on VASP outputs using the BaderKit package.
    """
    required_files = ["AECCAR0", "AECCAR2", "CHGCAR", "POTCAR"]
    use_previous_directory = ["AECCAR0", "AECCAR2", "CHGCAR", "POTCAR"]
    charge_filename = "CHGCAR"
    baderkit_class = Bader

