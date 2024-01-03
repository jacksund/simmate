# -*- coding: utf-8 -*-

from simmate.apps.quantum_espresso.workflows.base import PwscfWorkflow


class StaticEnergy__QuantumEspresso__Quality00(PwscfWorkflow):
    """
    A very a basic static energy calc for testing
    """

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
        ecutwfc__auto="efficiency",
        ecutrho__auto="efficiency",
    )

    electrons = dict(
        diagonalization="cg",
        mixing_mode="plain",
        mixing_beta=0.7,
        conv_thr="1.0e-8",
    )

    psuedo_mappings_set = "SSSP_PBE_EFFICIENCY"

    k_points = dict(
        spacing=0.5,
        gamma_centered=True,
    )
