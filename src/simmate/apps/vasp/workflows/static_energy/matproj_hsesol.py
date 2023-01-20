from simmate.apps.vasp.workflows.static_energy.matproj_hse import (
    StaticEnergy__Vasp__MatprojHse,
)


class StaticEnergy__Vasp__MatprojHsesol(StaticEnergy__Vasp__MatprojHse):
    """
    This task is a reimplementation of pymatgen's
    [MPHSERelaxSet](https://pymatgen.org/pymatgen.io.vasp.sets.html#pymatgen.io.vasp.sets.MPHSERelaxSet)
    but converted to a static energy calculation. The pymatgen library doesn't
    not have an HSEsol static energy, so this is the make-shift alternative.
    """

    incar = StaticEnergy__Vasp__MatprojHse.incar.copy()
    incar.update(dict(GGA="PS"))  # tells VASP to use PBEsol functional
