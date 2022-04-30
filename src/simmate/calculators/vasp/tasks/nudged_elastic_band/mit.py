# -*- coding: utf-8 -*-

from simmate.calculators.vasp.tasks.nudged_elastic_band.base import (
    VaspNudgedElasticBandTask,
)
from simmate.calculators.vasp.tasks.relaxation import MITRelaxation


class MITNudgedElasticBand(VaspNudgedElasticBandTask, MITRelaxation):
    """
    This task is a reimplementation of pymatgen's
    [MITNEBSet](https://pymatgen.org/pymatgen.io.vasp.sets.html#pymatgen.io.vasp.sets.MITNEBSet).

    Runs a NEB relaxation on a list of structures (aka images) using MIT Project
    settings. The lattice remains fixed and symmetry is turned off for this
    relaxation.

    You shouldn't use this workflow directly, but instead use the higher-level
    NEB workflows (e.g. diffusion/neb_all_paths or diffusion/neb_from_endpoints),
    which call this workflow for you.
    """

    incar = MITRelaxation.incar.copy()
    incar.update(
        dict(
            IBRION=1,
            ISYM=0,
            LCHARG=False,
            IMAGES__auto=True,
        )
    )
    incar.pop("multiple_keywords__smart_ldau")
