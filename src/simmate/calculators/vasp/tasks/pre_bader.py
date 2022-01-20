# -*- coding: utf-8 -*-

from simmate.calculators.vasp.tasks.energy.materials_project import MatProjStaticEnergy


class MatProjPreBaderTask(MatProjStaticEnergy):
    """
    Runs a static energy calculation with a high-density FFT grid under settings
    from the Materials Project. Results can be used for Bader analysis.

    We do NOT recommend running this calculation on its own. Instead, you should
    use the full workflow, which runs this calculation AND the following bader
    analysis for you. This S3Task is only the first step of that workflow.

    See `bader.workflows.materials_project`.
    """

    # The key thing for bader analysis is that we need a very fine FFT mesh. Other
    # than that, it's the same as a static energy calculation.
    incar = MatProjStaticEnergy.incar.copy()
    incar.update(
        NGXF__density_a=20,
        NGYF__density_b=20,
        NGZF__density_c=20,
    )
