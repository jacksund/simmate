# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------------------

from prefect import Client
from simmate.shortcuts import setup  # ensures setup
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

from simmate.shortcuts import setup
from simmate.database.diffusion import VaspCalcB

queryset = VaspCalcB.objects.filter(
    energy_barrier__isnull=True,
    pathway__structure__e_above_hull=0,
    pathway__empiricalmeasures__dimensionality__gte=2,
    pathway__vaspcalca__energy_barrier__lte=0.75,
).all()
from django_pandas.io import read_frame
df = read_frame(queryset)

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
from django_pandas.io import read_frame

# AB2 225
# AB3 194
# ABC4 123
#
# interesting 2D
# ABC 166 --dogwood
# ABCD 129 --longleaf
# AB2C2D2E2 139 --longleaf
# AB2C2 164 --dogwood
# AB2C4 139
# A2B3C7 139
#
# interesting 3D
# ABC3 221
#
queryset = (
    Pathway_DB.objects.filter(
        # structure__formula_anonymous="ABCD",
        # structure__chemical_system="Ca-F",
        # structure__spacegroup=129,
        structure__e_above_hull=0,
        empiricalmeasures__dimensionality__gte=2,
        vaspcalca__energy_barrier__lte=0.75,
        # vaspcalca__energy_barrier__gte=0,
        # vaspcalcb__energy_barrier__isnull=False,
        vaspcalcb__isnull=True,
        # vaspcalcc__isnull=False,
    ).order_by("vaspcalca__energy_barrier")
    # BUG: distinct() doesn't work for sqlite, only postgres. also you must have
    # "structure__id" as the first flag in order_by for this to work.
    .select_related("vaspcalca", "empiricalmeasures", "structure")
    # .distinct("structure__id")
    .all()
)
df = read_frame(
    queryset,
    fieldnames=[
        "id",
        "structure__formula_full",
        "structure__id",
        "structure__e_above_hull",
        "structure__spacegroup",
        "structure__formula_anonymous",
        "nsites_777",
        "nsites_101010",
        "vaspcalca__energy_barrier",
        "vaspcalcb__energy_barrier",
        "vaspcalcc__energy_barrier",
    ],
)


from simmate.shortcuts import setup
from simmate.database.diffusion import Pathway as Pathway_DB
from simmate.workflows.diffusion.utilities import get_oxi_supercell_path

# 51, 1686, 29326
# GOOD NEB: 77
# BAD NEB: 1046
pathway_id = 9504
path = Pathway_DB.objects.get(id=pathway_id)
get_oxi_supercell_path(path.to_pymatgen(), 10).write_path(
    f"{pathway_id}.cif",
    nimages=5,
    # idpp=True,
)

# import json
# from pymatgen.core.structure import Structure
# structure_dict = json.loads(path.vaspcalcb.structure_start_json)
# structure_start = Structure.from_dict(structure_dict)
# structure_start.to("cif", "z0.cif")
# structure_dict = json.loads(path.vaspcalcb.structure_midpoint_json)
# structure_midpoint = Structure.from_dict(structure_dict)
# structure_midpoint.to("cif", "z1.cif")
# structure_dict = json.loads(path.vaspcalcb.structure_end_json)
# structure_end = Structure.from_dict(structure_dict)
# structure_end.to("cif", "z2.cif")

# linear path from start to end
# images = structure_start.interpolate(structure_end, interpolate_lattices=True)
# test = [image.to(filename=f"{n}.cif") for n, image in enumerate(images)]


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
# from simmate.database.diffusion import VaspCalcC
# queryset = VaspCalcC.objects.get(pathway=26)
# pathway_ids = [1643,2791,1910,2688,2075,2338,3199,2511,3231,3186,2643]
# queryset = VaspCalcB.objects.filter(pathway__in=pathway_ids).all()


# import datetime
# from simmate.shortcuts import setup
# from simmate.database.diffusion import VaspCalcA
# queryset = VaspCalcA.objects.filter(status="S", updated_at__gte=datetime.date(2021,4,26)).all()
# from django_pandas.io import read_frame
# df = read_frame(queryset)


from optimade.providers.jarvis import JarvisStructure

structures = JarvisStructure.objects.filter(
    chemical_system="Y-C",
    nsites__lte=12,
    energy_above_hull=0,
    dimensionality_larsen=2,
).all()

structures.to_pymatgen()
structures.to_ase()
structures.to_pandas()


from jarvis.db.figshare import data

data_dft3d = data(dataset="dft_3d")
