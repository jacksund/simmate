# -*- coding: utf-8 -*-

# TO CREATE CONDA ENV...

# conda create -n simmate -c conda-forge python=3.8 numpy pandas django prefect dask click django-crispy-forms django-pandas psycopg2 dask-jobqueue scikit-learn pytest matplotlib plotly pymatgen spyder graphviz dj-database-url djangorestframework django-filter django-extensions

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

# from simmate.configuration.django.database import reset_database
# reset_database()

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
structure = Structure.from_file("nacl.cif")

# from pymatgen.io.vasp.sets import MPNonSCFSet
# mpset = MPNonSCFSet(structure, standardize=True)
# mpset.write_input("mpset")

# from simmate.calculators.vasp.tasks.bandstructure import BandStructureTask
# task = BandStructureTask(structure=structure, dir="smeset")
# result = task.run()

# from simmate.calculators.vasp.tasks.nudged_elastic_band import NudgedElasticBandTask
# task = NudgedElasticBandTask(structure=[structure for i in range(5)], dir="NEBset")
# result = task.run()


# import json
# data = json.load(open("db_dump.json"))
# for entry in data:
#     if entry["pk"] == "cod-1000023":
#         break
# from pymatgen.core.structure import Structure
# structure = Structure.from_str(entry["fields"]["structure_json"], "cif")

# import json

# data = json.load(open("db_dump.json"))

# ls = []
# for entry in data:
#     l = len(entry["fields"]["chemical_system"])
#     if l > 50:
#         # break
#         ls.append(entry["fields"]["chemical_system"])

