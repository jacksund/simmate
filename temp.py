# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------------------

# set the executor to a locally ran executor
# from prefect.executors import DaskExecutor
# workflow.executor = DaskExecutor(address="tcp://152.2.172.72:8786")

# --------------------------------------------------------------------------------------

# from simmate.shortcuts import setup
# from simmate.configuration.django.database import reset_database

# reset_database()

# --------------------------------------------------------------------------------------

# from simmate.shortcuts import setup
# from simmate.database.third_parties.scraping.cod import load_all_structures
# test = load_all_structures()

# --------------------------------------------------------------------------------------

from simmate.shortcuts import setup
from simmate.database.third_parties.all import MaterialsProjectStructure
from simmate.utilities import get_chemical_subsystems

MaterialsProjectStructure.objects.count()


systems = get_chemical_subsystems("Y-C-F")

MaterialsProjectStructure.objects.filter(chemical_system__in=systems).count()
MaterialsProjectStructure.objects.filter(chemical_system__contains="Y").filter(
    chemical_system__contains="C"
).count()

# --------------------------------------------------------------------------------------

from django.db.models import Sum

MaterialsProjectStructure.objects.aggregate(Sum("nsites"))

# --------------------------------------------------------------------------------------

from simmate.shortcuts import Structure_PMG
from simmate.calculators.vasp.tasks.base import VaspTask


class PreBaderTask(VaspTask):

    # The default settings to use for this static energy calculation.
    # The key thing for bader analysis is that we need a very fine FFT mesh
    # TODO: in the future, I will support a NGxyzF_density option inside of the
    # Incar class so that this grid is set based on the given structure.
    incar = dict(
        EDIFF=1.0e-07,
        EDIFFG=-1e-04,
        ENCUT=520,
        ISMEAR=0,
        LCHARG=True,
        LAECHG=True,
        LWAVE=False,
        NSW=0,
        PREC="Accurate",
        SIGMA=0.05,
        KSPACING=0.5,
        NGXF=100,
        NGYF=100,
        NGZF=100,
    )

    # We will use the PBE functional with all default mappings
    functional = "PBE"


structure = Structure_PMG.from_file("nacl.cif")

task = PreBaderTask()

result = task.run(structure=structure)

