# -*- coding: utf-8 -*-

from simmate.apps.quantum_espresso.workflows.relaxation.quality03 import (
    Relaxation__QuantumEspresso__Quality03,
)


class Relaxation__QuantumEspresso__Quality04(Relaxation__QuantumEspresso__Quality03):
    """
    Runs a somewhat rough Quantum Espresso geometry optimization with fixed lattice
    volume.

    `Quality 04` indicates that on a scale from 00 to 04, these are ranked 04 in
    quality (with 04 being the highest quality).

    Typically, you'd only want to run this relaxation on structures that were
    randomly created (and thus likely very unreasonable). More precise relaxations
    should be done afterwards. Therefore, instead of using this calculation,
    we recommend only using the relaxation/staged workflow, which uses this
    calculation as a fifth step.
    """

    description_doc_short = (
        "much less bare-bones settings for randomly-created structures"
    )

    control = dict(
        pseudo_dir__auto=True,  # uses the default directory for pseudopotentials
        restart_mode="from_scratch",  # start from new calc rather than restart
        calculation="vc-relax",  # perform geometry relaxation with variable cell
        tstress=True,  # calculate stress
        tprnfor=True,  # calculate forces
        nstep=100,  # maximum number of ionic steps
        etot_conv_thr="7.5e-6",  # Ionic step energy convergence threshold
        forc_conv_thr="7.5e-5",  # Ionic step force convergence threshhold
    )

    system = dict(
        ibrav=0,  # indicates crystal axis is provided in input
        nat__auto=True,  # automatically set number of atoms
        ntyp__auto=True,  # automatically set number of types of atoms
        ecutwfc__auto="efficiency_1.2",  # automatically select energy cutoff for wavefunctions
        ecutrho__auto="efficiency_1.2",  # automatically select energy cutoff for charge density/potential
        # We don't know if we have a metal or non-metal so we make a guess here.
        # !!! This guess could be dangerous without handlers
        multiple_keywords__smart_smear={
            "metal": dict(
                occupations="smearing",  # use smearing
                smearing="methfessel-paxton",  # equivalent to ISMEAR=1
                degauss=0.06,  # equivalent to SIGMA
            ),
            "non-metal": dict(
                occupations="smearing",  # Should we still use smearing here like we would in vasp?
                smearing="gaussian",  # equivalent to ISMEAR=0
                degauss=0.05,
            ),
        },
    )

    electrons = dict(
        diagonalization="david",  # equivalent to ALGO = Normal
        mixing_mode="plain",
        mixing_beta=0.7,  # mixing factor for self-consistency
        conv_thr="7.5e-7",  # convergence threshold for SCF cycle
    )

    k_points = dict(
        spacing=0.4,
        gamma_centered=True,
    )
