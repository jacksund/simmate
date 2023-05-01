```# Run this script as SLURM job. This script will handle submitting
# other workflows and will finish when ALL workflows finish.
#
# Check-list for this script:
#   1. use a postgres database
#   2. load the matproj database into your postgres database
#   3. start a bunch of simmate workers (or a "cluster")
#   4. submit this script as it's own slurm job

# Helpful links for the steps above:
#   1. https://jacksund.github.io/simmate/getting_started/use_a_cloud_database/build_a_postgres_database/
#   2. https://jacksund.github.io/simmate/getting_started/use_a_cloud_database/build_a_postgres_database/#vii-load-third-party-data
#   3. https://jacksund.github.io/simmate/getting_started/add_computational_resources/quick_start/

from simmate.database import connect
from simmate.database.third_parties import MatprojStructure
from simmate.workflows.utilities import get_workflow

# filter all the structures you want
structures = MatprojStructure.objects.filter(
    spacegroup=148,
    formula_reduced="ZnSnF6",
).all()

# as an extra, you can make this a pandas dataframe that you can easily
# view in spyder + write to a csv to open up in excel
data = structures.to_dataframe()
data.to_csv("mydata.csv")

# now let's run some workflows in parallel. To do this,
# make sure you are using a postgres database and
# have submitted a bunch of workers.
relax_workflow = get_workflow("relaxation.vasp.matproj")
relax_jobs = []
for structure in structures:
    status = relax_workflow.run_cloud(
        structure=structure,
        command="mpirun -n 8 vasp_std > vasp.out",
    )
    relax_jobs.append(status)

# once each job finishes, submit another workflow using the result
static_workflow = get_workflow("static-energy.vasp.matproj")
static_jobs = []
for job in relax_jobs:
    # BUG: This assumes all jobs will complete successfully! You may want a
    # try/except clause here that catched any jobs that failed.
    status = static_workflow.run_cloud(
        structure=job.result(),  # result() here says to wait for the job before to finish
        command="mpirun -n 8 vasp_std > vasp.out",
    )
    static_jobs.append(status)

# and do the same thing again with HSE band structure
hse_workflow = get_workflow("electronic-structure.vasp.matproj-full")
hse_jobs = []
for job in static_jobs:
    status = hse_workflow.run_cloud(
        structure=job.result(),  # result() here says to wait for the job before to finish
        command="mpirun -n 8 vasp_std > vasp.out",
    )
    hse_jobs.append(status)

# then you can have the job sit and wait for all results to finish
results = [job.result() for job in hse_jobs]
```
