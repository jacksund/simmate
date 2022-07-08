# -*- coding: utf-8 -*-

from simmate.toolkit import Structure
from simmate.calculators.vasp.inputs import Incar
from simmate.calculators.vasp.tasks.dynamics import MITDynamics


class MatVirtualLabNPTDynamics(MITDynamics):
    """
    This task is a reimplementation of pymatgen's
    [MVLNPTMDSet](https://pymatgen.org/pymatgen.io.vasp.sets.html#pymatgen.io.vasp.sets.MVLNPTMDSet).
    """

    confirm_convergence = False

    incar = MITDynamics.incar.copy()
    incar.update(
        dict(
            IALGO=48,
            ISIF=3,
            LANGEVIN_GAMMA__smart_langevin=True,
            LANGEVIN_GAMMA_L=1,
            MDALGO=3,
            PMASS=10,
            PSTRESS=0,
            SMASS=0,
            ENCUT=450,  # pymatgen sets to 1.5 * max of all potcars
        )
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
