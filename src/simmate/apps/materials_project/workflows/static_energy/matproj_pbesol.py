# -*- coding: utf-8 -*-

from simmate.apps.materials_project.workflows.static_energy.matproj import (
    StaticEnergy__Vasp__Matproj,
)


class StaticEnergy__Vasp__MatprojPbesol(StaticEnergy__Vasp__Matproj):
    """
    This task is a reimplementation of pymatgen's
    [MPStaticSet](https://pymatgen.org/pymatgen.io.vasp.sets.html#pymatgen.io.vasp.sets.MPStaticSet).

    The pymatgen library doesn't have a PBEsol static energy, so this is the
    make-shift alternative.
    """

    # tell VASP to use PBEsol functional
    _incar_updates = dict(GGA="PS")
