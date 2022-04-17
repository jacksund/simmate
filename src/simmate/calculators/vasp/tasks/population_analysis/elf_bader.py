# -*- coding: utf-8 -*-

from simmate.calculators.vasp.tasks.population_analysis.pre_bader import (
    MatProjPreBader,
)


class MatProjPreBaderELF(MatProjPreBader):
    """
    Runs a static energy calculation with a high-density FFT grid under settings
    from the Materials Project. Results can be used for Bader analysis where
    the ELF is used as the reference instead of the CHGCAR.
    """

    incar = MatProjPreBader.incar.copy()
    incar.update(
        LELF=True,  # writes ELFCAR
        NPAR=1,  # must be set if LELF is set to True
        PREC="Single",  # ensures CHGCAR grid matches ELFCAR grid
    )
