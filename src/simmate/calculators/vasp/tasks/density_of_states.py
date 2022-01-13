# -*- coding: utf-8 -*-

from simmate.calculators.vasp.tasks.energy.materials_project import (
    MatProjStaticEnergy,
)


class MatProjDensityOfStates(MatProjStaticEnergy):

    # Settings are based off of pymatgen's NonSCFSet in uniform mode
    incar = MatProjStaticEnergy.incar.copy()
    incar.update(
        ICHARGE=11,
        ISYM=2,
        NEDOS=2001,
    )
    incar.pop("MAGMOM__smart_magmom")
