# -*- coding: utf-8 -*-

from simmate.apps.materials_project.workflows.dynamics.mit import Dynamics__Vasp__Mit
from simmate.apps.vasp.inputs import Incar
from simmate.toolkit import Structure


class Dynamics__Vasp__MvlNpt(Dynamics__Vasp__Mit):
    """
    This task is a reimplementation of pymatgen's
    [MVLNPTMDSet](https://pymatgen.org/pymatgen.io.vasp.sets.html#pymatgen.io.vasp.sets.MVLNPTMDSet).
    """

    _incar_updates = dict(
        ALGO="Fast",
        ISIF=3,
        LANGEVIN_GAMMA__smart_langevin=True,
        LANGEVIN_GAMMA_L=1,
        MDALGO=3,
        PMASS=10,
        PSTRESS=0,
        SMASS=0,
        ENCUT=450,  # pymatgen sets to 1.5 * max of all potcars
    )


def keyword_modifier_smart_langevin(
    structure: Structure,
    langevin_config: bool = True,  # not required
):
    """
    Expands LANGEVIN_GAMMA setting based on number of species present
    """
    return [10] * structure.ntypesp


Incar.add_keyword_modifier(keyword_modifier_smart_langevin)
