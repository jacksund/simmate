# -*- coding: utf-8 -*-

from .quality03 import (
    Relaxation__QuantumEspresso__Quality03,
)


class Relaxation__QuantumEspresso__Quality04(Relaxation__QuantumEspresso__Quality03):
    """
    Runs a somewhat rough Quantum Espresso geometry optimization with fixed lattice
    volume.

    `Quality 04` indicates that on a scale from 00 to 04, these are ranked 04 in
    quality (with 04 being the highest quality).

    Therefore, instead of using this calculation directly, we recommend using
    the relaxation/staged workflow, which uses this calculation as a fifth step.
    """

    accuracy_rating = 1

    description_doc_short = (
        "much less bare-bones settings for randomly-created structures"
    )

    # -------------------------------------------------------------------------

    control = dict(
        pseudo_dir__auto=True,
        restart_mode="from_scratch",
        calculation="vc-relax",
        tstress=True,
        tprnfor=True,
        nstep=100,
        etot_conv_thr="7.5e-6",
        forc_conv_thr="7.5e-5",
    )

    system = dict(
        ibrav=0,
        nat__auto=True,
        ntyp__auto=True,
        ecutwfc__auto="efficiency_1.2",
        ecutrho__auto="efficiency_1.2",
        multiple_keywords__smart_smear={
            "metal": dict(
                occupations="smearing",
                smearing="methfessel-paxton",
                degauss=0.06,
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
        conv_thr="7.5e-9",
    )

    k_points = dict(
        spacing=0.4,
        gamma_centered=True,
    )
