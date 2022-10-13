from simmate.calculators.vasp.inputs.potcar_mappings import PBE_ELEMENT_MAPPINGS
from simmate.calculators.vasp.workflows.base import VaspWorkflow


class Relaxation__Vasp__ClusterLowQRelaxation(VaspWorkflow):
    functional = "PBE"
    potcar_mappings = PBE_ELEMENT_MAPPINGS

    use_database = True

    incar = dict(
        IBRION=2,
        KSPACING=0.6,
        EDIFFG=-0.2,
        IVDW=11,
        PREC="Normal",
        LDAU="TRUE",
        LDAUTYPE=2,
        LDAUL={"Sc": 2},
        LDAUU={"Sc": 3.00},
        LDAUJ={"Sc": 0.00},
        LDAUPRINT=2,
        ISMEAR=-5,
        ALGO="Fast",
        EDIFF=1e-04,
        ENCUT=300,
        NELM=100,
        NSW=99,
        SIGMA=0.05,
        LASPH="True",
        LORBIT=11,
    )
