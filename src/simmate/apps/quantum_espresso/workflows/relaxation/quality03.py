# -*- coding: utf-8 -*-

from .quality02 import (
    Relaxation__QuantumEspresso__Quality02,
)


class Relaxation__QuantumEspresso__Quality03(Relaxation__QuantumEspresso__Quality02):
    """
    Runs a slightly rough Quantum Espresso geometry optimization with fixed lattice
    volume.

    `Quality 03` indicates that on a scale from 00 to 04, these are ranked 03 in
    quality (with 04 being the highest quality).

    Therefore, instead of using this calculation directly, we recommend using
    the relaxation/staged workflow, which uses this calculation as a fourth step.
    """

    accuracy_rating = 0.5

    description_doc_short = "less bare-bones settings for randomly-created structures"

    # -------------------------------------------------------------------------

    control = dict(
        pseudo_dir__auto=True,
        restart_mode="from_scratch",
        calculation="vc-relax",
        tstress=True,
        tprnfor=True,
        nstep=100,
        etot_conv_thr="7.5e-5",
        forc_conv_thr="7.5e-4",
    )

    system = dict(
        ibrav=0,
        nat__auto=True,
        ntyp__auto=True,
        ecutwfc__auto="efficiency_1.1",
        ecutrho__auto="efficiency_1.1",
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
        conv_thr="7.5e-8",
    )
