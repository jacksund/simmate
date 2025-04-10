
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

- [x] use a postgres database ([guide](/getting_started/use_a_cloud_database/build_a_postgres_database.md))
- [x] load the matproj database into your postgres database
- [x] start a bunch of simmate workers (or a "cluster") ([guide](/getting_started/add_computational_resources/quick_start.md))


## The script :rocket:

!!! info
    We recommend submitting this script as it's own slurm job! This script will handle submitting
    other workflows and will finish when ALL workflows finish. 
    
    Additionally, we run each job below with 8 cores, so our workers are also submitted to a SLURM cluster with n=8.

``` python
from simmate.database import connect
from simmate.apps.materials_project.models import MatprojStructure
from simmate.workflows.utilities import get_workflow

# filter all the structures you want
structures = MatprojStructure.objects.filter(
    spacegroup=148,
    formula_reduced="ZnSnF6",
).all()

# submit relaxations to cluster
relax_workflow = get_workflow("relaxation.vasp.matproj")
relax_jobs = []
for structure in structures:
    status = relax_workflow.run_cloud(
        structure=structure,
        command="mpirun -n 8 vasp_std > vasp.out",
    )
    relax_jobs.append(status)

# as jobs finish, submit a static-energy for each
static_workflow = get_workflow("static-energy.vasp.matproj")
static_jobs = []
for job in relax_jobs:
    status = static_workflow.run_cloud(
        # BUG: This assumes all jobs will complete successfully!
        structure=job.result(), 
        command="mpirun -n 8 vasp_std > vasp.out",
    )
    static_jobs.append(status)

# as jobs finish, submit a band structure + density of states
elec_workflow = get_workflow("electronic-structure.vasp.matproj-full")
elec_jobs = []
for job in static_jobs:
    status = elec_workflow.run_cloud(
        structure=job.result(),
        command="mpirun -n 8 vasp_std > vasp.out",
    )
    elec_jobs.append(status)

# wait for all results to finish
results = [job.result() for job in elec_jobs]
```
