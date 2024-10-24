# -*- coding: utf-8 -*-

from simmate.apps.quantum_espresso.workflows.relaxation.quality04 import (
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

    control = dict(
        pseudo_dir__auto=True,  # uses the default directory for pseudopotentials
        restart_mode="from_scratch",  # start from new calc rather than restart
        calculation="scf",  # perform static energy calc
        tstress=True,  # calculate stress
        tprnfor=True,  # calculate forces
    )

    system = dict(
        ibrav=0,  # indicates crystal axis is provided in input
        nat__auto=True,  # automatically set number of atoms
        ntyp__auto=True,  # automatically set number of types of atoms
        ecutwfc__auto="efficiency_1.2",  # automatically select energy cutoff for wavefunctions
        ecutrho__auto="efficiency_1.2",  # automatically select energy cutoff for charge density/potential
        occupations="tetrahedra",  # was "smearing - methfessel-paxton" for metals, "smearing - gaussian" for non-metals
        degauss=0.05,  # Not sure this does anything with "tetrahedra". Was 0.05 for non-metals, 0.06 for metals
    )
