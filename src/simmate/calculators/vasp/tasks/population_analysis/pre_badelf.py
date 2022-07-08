# -*- coding: utf-8 -*-

from simmate.calculators.vasp.tasks.static_energy.materials_project import (
    MatprojStaticEnergy,
)


class MatprojPreBaderELF(MatprojStaticEnergy):
    """
    Runs a static energy calculation with a high-density FFT grid under settings
    from the Materials Project. Results can be used for Bader analysis where
    the ELF is used as the reference instead of the CHGCAR.
    """

    # The key thing for bader analysis is that we need a very fine FFT mesh. Other
    # than that, it's the same as a static energy calculation.
    incar = MatprojStaticEnergy.incar.copy()
    incar.update(
        LAECHG=True,  # write core charge density to AECCAR0 and valence to AECCAR2
        LELF=True,  # writes ELFCAR
        NPAR=1,  # must be set if LELF is set to True
        PREC="Single",  # ensures CHGCAR grid matches ELFCAR grid
        # Note that these set the FFT grid while the pre-Bader task sets the
        # fine FFT grid (e.g. useds NGX instead of NGXF)
        NGX__density_a=12,
        NGY__density_b=12,
        NGZ__density_c=12,
    )
