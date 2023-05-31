
# Example 001

## About :star:

This script queries the Material Project database for all ZnSnF6 structures with spacegroup=148 and then runs a (i) relaxation, (ii) static-energy, and (iii) bandstructure + density of states calculation on each -- passing the results between each step.

| Key Info        |                                            |
| --------------- | ------------------------------------------ |
| Contributor     | Becca Radomsky                             |
| Github User     | [@becca9835](https://github.com/becca9835) |
| Last updated    | 2023.05.01                                 |
| Simmate Version | v0.13.2                                    |

## Prerequisites :rotating_light:

- [x] use a postgres database ([guide](/simmate/getting_started/use_a_cloud_database/build_a_postgres_database/))
- [x] load the matproj database into your postgres database ([guide](/simmate/getting_started/use_a_cloud_database/build_a_postgres_database/#vii-load-third-party-data))
- [x] start a bunch of simmate workers (or a "cluster") ([guide](/simmate/getting_started/add_computational_resources/quick_start/))


## The script :rocket:

!!! info
    We recommend submitting this script as it's own slurm job! This script will handle submitting
    other workflows and will finish when ALL workflows finish. 
    
    Additionally, we run each job below with 8 cores, so our workers are also submitted to a SLURM cluster with n=8.

``` python
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

# and do the same thing again with a band structure + density of states
elec_workflow = get_workflow("electronic-structure.vasp.matproj-full")
elec_jobs = []
for job in static_jobs:
    status = elec_workflow.run_cloud(
        structure=job.result(),  # result() here says to wait for the job before to finish
        command="mpirun -n 8 vasp_std > vasp.out",
    )
    elec_jobs.append(status)

# then you can have the job sit and wait for all results to finish
results = [job.result() for job in elec_jobs]
```
