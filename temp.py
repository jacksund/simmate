# -*- coding: utf-8 -*-

"""
- write 1st rough static flow
- write 1st rough NEB flow --> and model for relaxed path
- test NEB run
- launch 1st rough static flows (wait 2 days before launching NEBs)
- inspect database for known flouride conductors and prototype plots
- outline writing & figures
"""

# --------------------------------------------------------------------------------------


# from dask.distributed import Client
# from simmate.workflows.diffusion.empirical_measures import workflow
# from simmate.configuration.django import setup_full  # ensures setup
# from simmate.database.diffusion import Pathway as Pathway_DB

# # grab the pathway ids that I am going to submit
# pathway_ids = (
#     Pathway_DB.objects.filter(empiricalmeasures__isnull=True)
#     .order_by("structure__nsites", "nsites_777")
#     .values_list("id", flat=True)
#     .all()[:3000]  # if I want to limit the number I submit at a time
# )

# # setup my Dask cluster and connect to it. Make sure I have each work connect to
# # the database before starting
# client = Client(preload="simmate.configuration.dask.init_django_worker")

# # Run the find_paths workflow for each individual id
# client.map(
#     workflow.run,
#     [{"pathway_id": id} for id in pathway_ids],
#     pure=False,
# )

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
    )
    .order_by("nsites_777", "structure__nsites", "length")
    # BUG: distinct() doesn't work for sqlite, only postgres. also you must have
    # "structure__id" as the first flag in order_by for this to work.
    # .distinct("structure__id")
    .values_list("id", flat=True)
    .all()[:1000]
)

# connect to Prefect Cloud
client = Client()

# submit a run for each pathway
for pathway_id in pathway_ids:
    client.create_flow_run(
        flow_id="5422b96d-fbbe-4f61-820f-dec934a2dd6b",
        parameters={"pathway_id": pathway_id},
    )

# --------------------------------------------------------------------------------------


# from simmate.configuration.django import setup_full  # ensures setup
# from simmate.database.diffusion import EmpiricalMeasures
# queryset = EmpiricalMeasures.objects.all()
# from django_pandas.io import read_frame
# df = read_frame(queryset) # , index_col="pathway": df = df.rese

# from simmate.configuration.django import setup_full  # ensures setup
# from simmate.database.diffusion import VaspCalcA
# queryset = VaspCalcA.objects.all()
# from django_pandas.io import read_frame
# df = read_frame(queryset) # , index_col="pathway": df = df.rese

# # from dask.distributed import Client
# # client = Client(preload="simmate.configuration.dask.init_django_worker")


# set the executor to a locally ran executor
# from prefect.executors import DaskExecutor
# workflow.executor = DaskExecutor(address="tcp://152.2.172.72:8786")




from simmate.configuration.django import setup_full  # ensures setup
from simmate.database.diffusion import Pathway
from simmate.workflows.diffusion.utilities import (
    run_vasp_custodian_neb,
    get_oxi_supercell_path,
)

path_db = Pathway.objects.first()
path = path_db.to_pymatgen()
structures = path.get_structures(nimages=3)
path_supercell = get_oxi_supercell_path(path, min_sl_v=7)
images = path_supercell.get_structures(nimages=1, idpp=True)

run_vasp_custodian_neb(
    images,
    vasp_cmd="mpirun -n 16 vasp",
    # errorhandler_settings="no_handler",
    custom_incar_endpoints={"NPAR": 1, "EDIFF": 5e-5, "ISIF": 2},  # "NSW": 0,
    custom_incar_neb={"NPAR": 1, "EDIFF": 5e-5, "EDIFFG": -0.1, "ISIF": 2},
)



"""
PZUNMTR parameter number    5 had an illegal value 
{    0,    0}:  On entry to 
PZUNMTR parameter number    5 had an illegal value 
 GSD%LWWORK        1228        5116         456          76
 ERROR in subspace rotation PSSYEVX: not enough eigenvalues found         618


===================================================================================
=   BAD TERMINATION OF ONE OF YOUR APPLICATION PROCESSES
=   RANK 3 PID 3326541 RUNNING AT WarWulf
=   KILLED BY SIGNAL: 6 (Aborted)
===================================================================================


"""