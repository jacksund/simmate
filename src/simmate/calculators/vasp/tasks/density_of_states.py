# -*- coding: utf-8 -*-

from simmate.calculators.vasp.tasks.energy.materials_project import (
    MaterialsProjectStaticEnergy,
)


class MaterialsProjectDensityOfStatesTask(MaterialsProjectStaticEnergy):

    # Settings are based off of pymatgen's NonSCFSet in uniform mode
    incar = MaterialsProjectStaticEnergy.incar.copy()
    incar.update(
        ICHARGE=11,
        ISYM=2,
        NEDOS=2001,
    )
    incar.pop("MAGMOM__smart_magmom")
