# -*- coding: utf-8 -*-

from ..relaxation.quality04 import (
    Relaxation__QuantumEspresso__Quality04,
)


class StaticEnergy__QuantumEspresso__Quality04(Relaxation__QuantumEspresso__Quality04):
    """
    Runs a rough QuantumEspresso static energy calculation.

    `Quality 04` relates to our ranking of relaxation qualities, where this
    calculation uses the same settings as the Quality04 Relaxation.

    Note, even though this is currently our highest quality preset, these
    settings are still only suitable for high-throughput calculations or massive
    supercells. Settings are still below MIT and Materials Project quality.

    Most commonly, this is used in evolutionary searches (for structure
    prediction). We recommend instead using the relaxation/staged workflow,
    which uses this calculation as the sixth and final step -- after a series
    of rough relaxations are done.
    """

    accuracy_rating = 1

    control = dict(
        pseudo_dir__auto=True,
        restart_mode="from_scratch",
        calculation="scf",
        tstress=True,
        tprnfor=True,
    )

    system = dict(
        ibrav=0,
        nat__auto=True,
        ntyp__auto=True,
        ecutwfc__auto="efficiency_1.2",
        ecutrho__auto="efficiency_1.2",
        occupations="tetrahedra",
        degauss=0.05,
    )
