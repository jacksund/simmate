# -*- coding: utf-8 -*-

from simmate.calculators.vasp.tasks.energy.materials_project import MatProjStaticEnergy


class MatProjPreBaderTask(MatProjStaticEnergy):

    # The key thing for bader analysis is that we need a very fine FFT mesh. Other
    # than that, it's the same as a static energy calculation.
    incar = MatProjStaticEnergy.incar.copy()
    incar.update(
        NGXF__density_a=20,
        NGYF__density_a=20,
        NGZF__density_a=20,
    )
