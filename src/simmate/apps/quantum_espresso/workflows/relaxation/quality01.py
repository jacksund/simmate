# -*- coding: utf-8 -*-

from .quality00 import (
    Relaxation__QuantumEspresso__Quality00,
)


class Relaxation__QuantumEspresso__Quality01(Relaxation__QuantumEspresso__Quality00):
    """
    Runs a pretty rough Quantum Espresso geometry optimization with fixed lattice
    volume.

    `Quality 01` indicates that on a scale from 00 to 04, these are ranked 01 in
    quality (with 04 being the highest quality).

    Typically, you'd only want to run this relaxation on structures that were
    randomly created (and thus likely very unreasonable). More precise relaxations
    should be done afterwards. Therefore, instead of using this calculation,
    we recommend only using the relaxation/staged workflow, which uses this
    calculation as a second step.
    """

    accuracy_rating = 0.5

    description_doc_short = "bare-bones settings for randomly-created structures"

    # -------------------------------------------------------------------------

    control = dict(
        pseudo_dir__auto=True,
        restart_mode="from_scratch",
        calculation="relax",
        tstress=True,
        tprnfor=True,
        nstep=75,
        etot_conv_thr="7.5e-4",
        forc_conv_thr="7.5e-3",
    )

    system = dict(
        ibrav=0,
        nat__auto=True,
        ntyp__auto=True,
        ecutwfc__auto="efficiency_0.9",
        ecutrho__auto="efficiency_0.9",
        multiple_keywords__smart_smear={
            "metal": dict(
                occupations="smearing",
                smearing="methfessel-paxton",
                degauss=0.08,
            ),
            "non-metal": dict(
                occupations="smearing",
                smearing="gaussian",
                degauss=0.05,
            ),
        },
    )

    electrons = dict(
        diagonalization="david",
        mixing_mode="plain",
        mixing_beta=0.7,
        conv_thr="7.5e-7",
    )

    k_points = dict(
        spacing=0.6,
        gamma_centered=True,
    )
