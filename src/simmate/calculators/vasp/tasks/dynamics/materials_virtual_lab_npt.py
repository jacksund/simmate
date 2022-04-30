# -*- coding: utf-8 -*-

from simmate.calculators.vasp.tasks.dynamics import MITDynamics


class MatVirtualLabNPTDynamics(MITDynamics):
    """
    This task is a reimplementation of pymatgen's
    [MVLNPTMDSet](https://pymatgen.org/pymatgen.io.vasp.sets.html#pymatgen.io.vasp.sets.MVLNPTMDSet).
    """

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
