# -*- coding: utf-8 -*-

# TO CREATE CONDA ENV...

# conda create -n simmate -c conda-forge python=3.8 numpy pandas django prefect dask click django-crispy-forms django-pandas psycopg2 dask-jobqueue scikit-learn pytest matplotlib plotly pymatgen spyder graphviz dj-database-url djangorestframework django-filter django-extensions pyyaml gunicorn

# pymatgen-diffusion is outdated on anaconda
# pip install pymatgen-analysis-diffusion

# other packages for pulling data
# pip install jarvis-tools

# git clone https://github.com/jacksund/simmate.git
# pip install -e simmate

# --------------------------------------------------------------------------------------

# TO RUN DJANGO SERVER...
# django-admin runserver --settings=simmate.configuration.django.settings

# --------------------------------------------------------------------------------------

# set the executor to a locally ran executor
# from prefect.executors import DaskExecutor
# workflow.executor = DaskExecutor(address="tcp://152.2.172.72:8786")

# --------------------------------------------------------------------------------------

from simmate.configuration.django.database import reset_database
reset_database()

# --------------------------------------------------------------------------------------

from simmate.shortcuts import setup
from simmate.database.third_parties.scraping.materials_project import load_all_structures
load_all_structures()

# --------------------------------------------------------------------------------------

from simmate.shortcuts import setup
from simmate.database.third_parties.all import MaterialsProjectStructure
MaterialsProjectStructure.objects.count()

from simmate.utilities import get_chemical_subsystems
systems = get_chemical_subsystems("Y-C-F")
MaterialsProjectStructure.objects.filter(chemical_system__in=systems).count()
MaterialsProjectStructure.objects.filter(chemical_system__contains="Y").filter(
    chemical_system__contains="C"
).count()

# --------------------------------------------------------------------------------------

from django.db.models import Sum

MaterialsProjectStructure.objects.aggregate(Sum("nsites"))

# --------------------------------------------------------------------------------------

from simmate.shortcuts import setup
from simmate.database.third_parties.all import MaterialsProjectStructure
queryset = MaterialsProjectStructure.objects.all()[:100]
from django_pandas.io import read_frame
df = read_frame(queryset)

# --------------------------------------------------------------------------------------

from simmate.shortcuts import Structure_PMG
from simmate.calculators.vasp.tasks.base import VaspTask


class PreBaderTask(VaspTask):

    # The default settings to use for this static energy calculation.
    # The key thing for bader analysis is that we need a very fine FFT mesh
    # TODO: in the future, I will support a NGxyzF__density option inside of the
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

# load the structure
structure = Structure_PMG.from_file("nacl.cif")

# Initialize the task
task = PreBaderTask(command="mpirun -n 4 vasp > vasp.out")

# Now run the task with your desired structure and directory
result = task.run(structure=structure, dir=".")

# --------------------------------------------------------------------------------------

from pymatgen.core.structure import Structure
structure = Structure.from_file("YFeO3.cif")

from simmate.calculators.vasp.inputs.all import Incar

incar = Incar(
    ALGO="Fast",
    EDIFF=1.0e-05,
    ENCUT=520,
    IBRION=2,
    ICHARG=1,
    ISIF=3,
    ISMEAR=-5,
    ISPIN=2,
    ISYM=0,
    LORBIT=11,
    LREAL="Auto",
    LWAVE=False,
    NELM=200,
    NELMIN=6,
    NSW=99,
    PREC="Accurate",
    SIGMA=0.05,
    MAGMOM__smart_magmom={
        "default": 0.6,
        "Ce": 5,
        "Ce3+": 1,
        "Co": 0.6,
        "Co3+": 0.6,
        "Co4+": 1,
        "Cr": 5,
        "Dy3+": 5,
        "Er3+": 3,
        "Eu": 10,
        "Eu2+": 7,
        "Eu3+": 6,
        "Fe": 5,
        "Gd3+": 7,
        "Ho3+": 4,
        "La3+": 0.6,
        "Lu3+": 0.6,
        "Mn": 5,
        "Mn3+": 4,
        "Mn4+": 3,
        "Mo": 5,
        "Nd3+": 3,
        "Ni": 5,
        "Pm3+": 4,
        "Pr3+": 2,
        "Sm3+": 5,
        "Tb3+": 6,
        "Tm3+": 2,
        "V": 5,
        "W": 5,
        "Yb3+": 1,
        },
    multiple_keywords__smart_ldau=dict(
        LDAU__auto=True,
        LDAUTYPE=2,
        LDAUPRINT=1,
        LMAXMIX__auto=True,
        LDAUJ={},
        LDAUL={
            "F":{
                "Ag":2,
                "Co":2,
                "Cr":2,
                "Cu":2,
                "Fe":2,
                "Mn":2,
                "Mo":2,
                "Nb":2,
                "Ni":2,
                "Re":2,
                "Ta":2,
                "V":2,
                "W":2,
                },
            "O":{
                "Ag":2,
                "Co":2,
                "Cr":2,
                "Cu":2,
                "Fe":2,
                "Mn":2,
                "Mo":2,
                "Nb":2,
                "Ni":2,
                "Re":2,
                "Ta":2,
                "V":2,
                "W":2,
                },
            "S":{
                "Fe":2,
                "Mn":2.5,
            },
        },
        LDAUU={
            "F":{
                "Ag":1.5,
                "Co":3.4,
                "Cr":3.5,
                "Cu":4,
                "Fe":4.0,
                "Mn":3.9,
                "Mo":4.38,
                "Nb":1.5,
                "Ni":6,
                "Re":2,
                "Ta":2,
                "V":3.1,
                "W":4.0,
                },
            "O":{
                "Ag":1.5,
                "Co":3.4,
                "Cr":3.5,
                "Cu":4,
                "Fe":4.0,
                "Mn":3.9,
                "Mo":4.38,
                "Nb":1.5,
                "Ni":6,
                "Re":2,
                "Ta":2,
                "V":3.1,
                "W":4.0,
                },
            "S":{
                "Fe":1.9,
                "Mn":2.5,
                },
            }
        ),
    )

print(incar.__str__(structure=structure))

from pymatgen.io.vasp.sets import MITRelaxSet
mp = MITRelaxSet(structure)
print(mp.incar)

# from pymatgen.io.vasp.sets import MPNonSCFSet
# mpset = MPNonSCFSet(structure, standardize=True)
# mpset.write_input("mpset")

# from simmate.calculators.vasp.tasks.bandstructure import BandStructureTask
# task = BandStructureTask(structure=structure, dir="smeset")
# result = task.run()

# from simmate.calculators.vasp.tasks.nudged_elastic_band import NudgedElasticBandTask
# task = NudgedElasticBandTask(structure=[structure for i in range(5)], dir="NEBset")
# result = task.run()
