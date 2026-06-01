# -*- coding: utf-8 -*-

from .quality01 import (
    Relaxation__QuantumEspresso__Quality01,
)


class Relaxation__QuantumEspresso__Quality02(Relaxation__QuantumEspresso__Quality01):
    """
    Runs a rough Quantum Espresso geometry optimization with fixed lattice
    volume.

    `Quality 02` indicates that on a scale from 00 to 04, these are ranked 02 in
    quality (with 04 being the highest quality).

    Typically, you'd only want to run this relaxation on structures that were
    randomly created (and thus likely very unreasonable). More precise relaxations
    should be done afterwards. Therefore, instead of using this calculation,
    we recommend only using the relaxation/staged workflow, which uses this
    calculation as a third step.
    """

    accuracy_rating = 0.5

    description_doc_short = (
        "slightly less bare-bones settings for randomly-created structures"
    )

    # -------------------------------------------------------------------------

    symmetry_precision = 0.1

    control = dict(
        pseudo_dir__auto=True,
        restart_mode="from_scratch",
        calculation="vc-relax",
        tstress=True,
        tprnfor=True,
        nstep=100,
        etot_conv_thr="7.5e-4",
        forc_conv_thr="7.5e-3",
    )

    system = dict(
        ibrav=0,
        nat__auto=True,
        ntyp__auto=True,
        ecutwfc__auto="efficiency",
        ecutrho__auto="efficiency",
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

    cell = dict(cell_dynamics="bfgs")

    k_points = dict(
        spacing=0.5,
        gamma_centered=True,
    )
