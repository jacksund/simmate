# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------------------

from prefect import Client
from simmate.shortcuts import setup # ensures setup
from simmate.database.diffusion import Pathway as Pathway_DB

# grab the pathway ids that I am going to submit
pathway_ids = (
    Pathway_DB.objects.filter(
        vaspcalca__isnull=True,
        empiricalmeasures__dimensionality__gte=1,
        # empiricalmeasures__oxidation_state=-1,
        # empiricalmeasures__ionic_radii_overlap_cations__gt=-1,
        # empiricalmeasures__ionic_radii_overlap_anions__gt=-1,
        # nsites_777__lte=150,
        # structure__nsites__lte=20,
    ).order_by("nsites_777", "structure__nsites", "length")
    # BUG: distinct() doesn't work for sqlite, only postgres. also you must have
    # "structure__id" as the first flag in order_by for this to work.
    # .distinct("structure__id")
    .values_list("id", flat=True)
    # .count()
    .all()[:500]
)

# connect to Prefect Cloud
client = Client()

# submit a run for each pathway
for pathway_id in pathway_ids:
    client.create_flow_run(
        flow_id="dae896f1-2078-4389-8383-0a3dab61ef2b",
        parameters={"pathway_id": pathway_id},
    )

# --------------------------------------------------------------------------------------


# from simmate.configuration.django import setup_full  # ensures setup
# from simmate.database.diffusion import EmpiricalMeasures
# queryset = EmpiricalMeasures.objects.all()  # [:5000]
# from django_pandas.io import read_frame
# df = read_frame(queryset)  # , index_col="pathway"

# from simmate.shortcuts import setup
# from simmate.database.diffusion import VaspCalcB
# queryset = VaspCalcB.objects.all()
# from django_pandas.io import read_frame
# df = read_frame(queryset)

# from simmate.shortcuts import setup
# from simmate.database.diffusion import VaspCalcA
# pids = [14695, 15038]
# queryset = VaspCalcA.objects.filter(pathway_id__in=pids).all()


# --------------------------------------------------------------------------------------

# .filter(pathway_id__in=pids)
# pids= [3036,
# 9461,
# 3040,
# 10373,
# 3033,
# 8701,
# 9143,
# 9924,
# 1220,
# 1443,
# 1496,
# 1034,]

from simmate.shortcuts import setup
from simmate.database.diffusion import Pathway as Pathway_DB
# AB2 225
# AB3 194
# ABC4 123
queryset = (
    Pathway_DB.objects.filter(
        # structure__formula_anonymous="ABC2",
        # structure__chemical_system="Ca-F",
        # structure__spacegroup=194,
        empiricalmeasures__dimensionality=3,
        vaspcalca__energy_barrier__lte=2,
        vaspcalca__energy_barrier__gte=0,
        # vaspcalcb__energy_barrier__isnull=True,
        vaspcalcb__isnull=True,
    )
    .order_by("vaspcalca__energy_barrier")
    # BUG: distinct() doesn't work for sqlite, only postgres. also you must have
    # "structure__id" as the first flag in order_by for this to work.
    .select_related("vaspcalca", "empiricalmeasures")
    # .distinct("structure__id")
    .all()
)
# .to_pymatgen().write_path("test.cif", nimages=3)
from django_pandas.io import read_frame
df = read_frame(
    queryset,
    fieldnames=[
        "id",
        "structure__formula_full",
        "structure__id",
        "vaspcalca__energy_barrier",
        "nsites_101010",
        # "vaspcalcb__energy_barrier",
    ],
)


# from simmate.shortcuts import setup
# from simmate.database.diffusion import Pathway as Pathway_DB
# from simmate.workflows.diffusion.utilities import get_oxi_supercell_path
# # 51, 1686, 29326
# get_oxi_supercell_path(
#     Pathway_DB.objects.get(id=3020).to_pymatgen(), 9).write_path(
#     "test.cif",
#     nimages=3,
#     # idpp=True,
# )


# from simmate.database.diffusion import Pathway as Pathway_DB
# path_db = Pathway_DB.objects.get(id=55).to_pymatgen().write_path("test.cif", nimages=3)

# set the executor to a locally ran executor
# from prefect.executors import DaskExecutor
# workflow.executor = DaskExecutor(address="tcp://152.2.172.72:8786")

# from simmate.shortcuts import setup  # ensures setup
# from simmate.database.diffusion import Pathway
# from simmate.workflows.diffusion.vaspcalc_b import workflow
# result = workflow.run(pathway_id=4, vasp_cmd="mpirun -n 16 vasp_std")

# module load openmpi_3.0.0/gcc_6.3.0
# mpirun -n 44 /21dayscratch/scr/j/a/jacksund/vasp_build/vasp/5.4.4/bin/vasp

# from simmate.shortcuts import setup
# from simmate.database.diffusion import VaspCalcB
# queryset = VaspCalcB.objects.get(pathway=15436)
# pathway_ids = [2080,2082, 2085, 2644, 2645, 2646, 2756, 2762, 3051, 3052]
# queryset = VaspCalcB.objects.filter(pathway__in=pathway_ids).all()


# import datetime
# from simmate.shortcuts import setup
# from simmate.database.diffusion import VaspCalcA
# queryset = VaspCalcA.objects.filter(status="S", updated_at__gte=datetime.date(2021,4,26)).all()
# from django_pandas.io import read_frame
# df = read_frame(queryset)
    