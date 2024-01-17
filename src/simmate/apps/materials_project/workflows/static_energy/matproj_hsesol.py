from simmate.apps.materials_project.workflows.static_energy.matproj_hse import (
    StaticEnergy__Vasp__MatprojHse,
)


class StaticEnergy__Vasp__MatprojHsesol(StaticEnergy__Vasp__MatprojHse):
    """
    This task is a reimplementation of pymatgen's
    [MPHSERelaxSet](https://pymatgen.org/pymatgen.io.vasp.sets.html#pymatgen.io.vasp.sets.MPHSERelaxSet)
    but converted to a static energy calculation. The pymatgen library doesn't
    not have an HSEsol static energy, so this is the make-shift alternative.
    """

    # tells VASP to use PBEsol functional
    _incar_updates = dict(GGA="PS")
