from simmate.calculators.vasp.inputs.potcar_mappings import PBE_ELEMENT_MAPPINGS
from simmate.calculators.vasp.workflows.base import VaspWorkflow


class StaticEnergy__Vasp__ClusterStaticEnergy(VaspWorkflow):
    functional = "PBE"
    potcar_mappings = PBE_ELEMENT_MAPPINGS

    use_database = True

    incar = dict(
        IBRION=-1,
        KSPACING=0.4,
        EDIFFG=-0.02,
        IVDW=11,
        PREC="Accurate",
        LDAU="TRUE",
        LDAUTYPE=2,
        LDAUL={"Sc": 2},
        LDAUU={"Sc": 3.00},
        LDAUJ={"Sc": 0.00},
        LDAUPRINT=2,
        ISMEAR=-5,
        ALGO="Normal",
        EDIFF=1e-07,
        ENCUT=500,
        NELM=100,
        NSW=0,
        SIGMA=0.05,
        LASPH="True",
        LORBIT=11,
    )
