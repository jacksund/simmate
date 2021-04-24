# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------------------

from prefect import Client
from simmate.configuration.django import setup_full  # ensures setup
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
    .all()[:300]
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

# from simmate.configuration.django import setup_full  # ensures setup
# from simmate.database.diffusion import VaspCalcA
# queryset = VaspCalcA.objects.all()
# from django_pandas.io import read_frame
# df = read_frame(queryset)
# df.hist("energy_barrier", bins=100, figsize=(10,2))


# --------------------------------------------------------------------------------------


from simmate.configuration.django import setup_full  # ensures setup
from simmate.database.diffusion import Pathway as Pathway_DB

queryset = (
    Pathway_DB.objects.filter(
        vaspcalca__energy_barrier__isnull=False,
        vaspcalca__energy_barrier__gte=0,
        empiricalmeasures__ionic_radii_overlap_anions__gt=-900,
    )
    .select_related("vaspcalca", "empiricalmeasures")
    .all()
)
from django_pandas.io import read_frame

df = read_frame(
    queryset,
    fieldnames=[
        "length",
        "empiricalmeasures__ewald_energy",
        "empiricalmeasures__ionic_radii_overlap_anions",
        "empiricalmeasures__ionic_radii_overlap_cations",
        "vaspcalca__energy_barrier",
    ],
)
df.plot(
    x="empiricalmeasures__ewald_energy",
    y="vaspcalca__energy_barrier",
    kind="scatter",
    s=4,
    # xlim=(0,1.2),
    # ylim=(0,17),
)
df.plot(
    x="empiricalmeasures__ionic_radii_overlap_anions",
    y="empiricalmeasures__ionic_radii_overlap_cations",
    c="vaspcalca__energy_barrier",
    kind="scatter",
    colormap="RdYlGn_r",
)
df.plot(
    x="empiricalmeasures__ionic_radii_overlap_anions",
    y="vaspcalca__energy_barrier",
    c="empiricalmeasures__ionic_radii_overlap_cations",
    kind="scatter",
    colormap="RdYlGn_r",
)
df.plot(
    x="empiricalmeasures__ionic_radii_overlap_cations",
    y="vaspcalca__energy_barrier",
    c="empiricalmeasures__ionic_radii_overlap_anions",
    kind="scatter",
    colormap="RdYlGn_r",
)
df.plot.hexbin(
    x="empiricalmeasures__ionic_radii_overlap_anions",
    y="empiricalmeasures__ionic_radii_overlap_cations",
    C="vaspcalca__energy_barrier",
    gridsize=20,
    colormap="RdYlGn_r",
    vmax=7.5,
)





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

queryset = (
    Pathway_DB.objects.filter(
        structure__formula_anonymous="AB2",
        # structure__chemical_system="Ca-F",
        structure__spacegroup=225,
        vaspcalca__energy_barrier__lte=2,
    ).all()
    # .to_pymatgen()
    # .write_path("test.cif", nimages=3)
)
from django_pandas.io import read_frame

df = read_frame(
    queryset,
    fieldnames=[
        "id",
        "structure__formula_full",
        "structure__id",
        "vaspcalca__energy_barrier",
    ],
)

# from simmate.database.diffusion import Pathway as Pathway_DB
# path_db = Pathway_DB.objects.get(id=55).to_pymatgen().write_path("test.cif", nimages=3)

# set the executor to a locally ran executor
# from prefect.executors import DaskExecutor
# workflow.executor = DaskExecutor(address="tcp://152.2.172.72:8786")

# from simmate.configuration.django import setup_full  # ensures setup
# from simmate.database.diffusion import Pathway
# from simmate.workflows.diffusion.vaspcalc_b import workflow
# result = workflow.run(pathway_id=4)

