from simmate.apps.vasp.inputs import PBE_POTCAR_MAPPINGS
from simmate.apps.vasp.workflows.base import VaspWorkflow


class StaticEnergy__Vasp__ClusterHighQe(VaspWorkflow):
    functional = "PBE"
    potcar_mappings = PBE_POTCAR_MAPPINGS

    _incar = dict(
        IBRION=-1,
        KSPACING=0.4,
        EDIFFG=-0.02,
        IVDW=11,
        PREC="Accurate",
        ISMEAR=-5,
        ALGO="Normal",
        EDIFF=1e-07,
        ENCUT=500,
        NELM=100,
        NSW=0,
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
