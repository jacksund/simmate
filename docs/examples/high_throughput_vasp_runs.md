
# High-Throughput VASP Runs

## About :star:

This script demonstrates how to automate a series of VASP calculations across many structures. We query the Materials Project database for a specific set of materials and then chain together (i) relaxation, (ii) static-energy, and (iii) electronic structure workflows for each.

| Key Info        |                                            |
| --------------- | ------------------------------------------ |
| Contributor     | Becca Radomsky                             |
| Github User     | [@becca9835](https://github.com/becca9835) |
| Last updated    | 2026.03.14                                 |
| Level           | **Intermediate**                           |

## Prerequisites :rotating_light:

- [x] Configure a database ([guide](/getting_started/workflows/configure_database.md))
- [x] Load Materials Project data ([guide](/database/access_thirdparty_data.md))
- [x] Simulation software installed (VASP)
- [x] Simmate workers running ([guide](/getting_started/add_computational_resources/quickstart.md))

## The script :rocket:

!!! info
    This script uses `run_cloud` to submit jobs to your database. These jobs will be picked up and executed by your running workers.

``` python
from simmate.database import connect
from simmate.apps.materials_project.models import MatprojStructure
from simmate.workflows.utils import get_workflow

# 1. Query the structures we want to study
# Here we find all ZnSnF6 structures with spacegroup 148.
structures = MatprojStructure.objects.filter(
    spacegroup__number=148,
    formula_reduced="ZnSnF6",
).all()

# 2. Submit relaxations to the cluster
relax_workflow = get_workflow("relaxation.vasp.matproj")
relax_states = []
for structure in structures:
    state = relax_workflow.run_cloud(
        structure=structure,
        command="mpirun -n 8 vasp_std > vasp.out",
    )
    relax_states.append(state)

# 3. As relaxations finish, submit static-energy jobs
static_workflow = get_workflow("static-energy.vasp.matproj")
static_states = []
for state in relax_states:
    # .result() will wait until the relaxation is finished
    relaxed_structure = state.result() 
    
    new_state = static_workflow.run_cloud(
        structure=relaxed_structure, 
        command="mpirun -n 8 vasp_std > vasp.out",
    )
    static_states.append(new_state)

# 4. Finally, submit electronic structure jobs (Bands + DOS)
elec_workflow = get_workflow("electronic-structure.vasp.matproj-full")
for state in static_states:
    static_structure = state.result()
    
    elec_workflow.run_cloud(
        structure=static_structure,
        command="mpirun -n 8 vasp_std > vasp.out",
    )

print("All jobs have been submitted to the cluster!")
```
