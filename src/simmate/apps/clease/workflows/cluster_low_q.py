from simmate.apps.vasp.inputs import PBE_POTCAR_MAPPINGS
from simmate.apps.vasp.workflows.base import VaspWorkflow


class Relaxation__Vasp__ClusterLowQ(VaspWorkflow):
    functional = "PBE"
    potcar_mappings = PBE_POTCAR_MAPPINGS

    incar = dict(
        IBRION=2,
        KSPACING=0.6,
        EDIFFG=-0.2,
        IVDW=11,
        PREC="Normal",
        ISMEAR=-5,
        ALGO="Fast",
        EDIFF=1e-04,
        ENCUT=300,
        NELM=100,
        NSW=99,
        SIGMA=0.05,
        LASPH=True,
        LORBIT=11,
        multiple_keywords__smart_ldau=dict(
            LDAU__auto=True,
            LDAUTYPE=2,
            LDAUPRINT=2,
            LDAUJ={"C": {"Sc": 0}},
            LDAUL={"C": {"Sc": 2}},
            LDAUU={"C": {"Sc": 3.0}},
        ),
    )
