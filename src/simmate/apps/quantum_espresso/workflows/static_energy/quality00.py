# -*- coding: utf-8 -*-

from simmate.apps.quantum_espresso.workflows.base import PwscfWorkflow


class StaticEnergy__QuantumEspresso__Quality00(PwscfWorkflow):
    # just a basic static energy for me to test with

    control = dict(
        pseudo_dir="__auto__",
        restart_mode="from_scratch",
        calculation="scf",
        tstress=True,
        tprnfor=True,
    )

    system = dict(
        ibrav=0,
        nat=2,
        ntyp=1,
        ecutwfc=18.0,
    )

    electrons = dict(
        diagonalization="cg",
        mixing_mode="plain",
        mixing_beta=0.7,
        conv_thr="1.0e-8",
    )
