
# Custom Evolutionary Search

## About :star:

This script demonstrates how to set up and customize a crystal structure prediction (CSP) search. We configure an evolutionary search for a fixed composition (Ca2N), specifying custom mutation rates and stop conditions.

| Key Info        |                                            |
| --------------- | ------------------------------------------ |
| Contributor     | Simmate Team                               |
| Last updated    | 2026.03.14                                 |
| Level           | **Advanced**                               |

## Prerequisites :rotating_light:

- [x] Configure a database ([guide](/getting_started/workflows/configure_database.md))
- [x] Simulation software installed (VASP)
- [x] Simmate workers running ([guide](/getting_started/add_computational_resources/quick_start.md))

## The script :rocket:

``` python
from simmate.workflows.utilities import get_workflow

# 1. Get the evolutionary search workflow
# This runs a search for a fixed composition and number of sites.
search_workflow = get_workflow("structure-prediction.toolkit.fixed-composition")

# 2. Configure and run the search
# We customize many of the search parameters here.
state = search_workflow.run(
    composition="Ca2N",
    
    # Use a specific VASP workflow for relaxing each new individual
    subworkflow_name="relaxation.vasp.matproj",
    subworkflow_kwargs={
        "command": "mpirun -n 4 vasp_std > vasp.out",
    },
    
    # Customize the steady-state mutation rates (must add up to 1.0)
    steadystate_sources={
        "RandomSymStructure": 0.40,
        "from_ase.Heredity": 0.40,
        "from_ase.SoftMutation": 0.10,
        "from_ase.LatticeStrain": 0.10,
    },
    
    # Set custom stop conditions
    stop_conditions={
        "BasicStopConditions": {
            "max_structures": 100,      # stop after 100 structures
            "convergence_cutoff": 0.01, # or if the best energy is stable
        }
    },
    
    # Initial random generation size
    nfirst_generation=20,
    
    # Number of structures to keep in the population
    nsteadystate=40,
)

# 3. Monitor the results
# The search runs in the background. Results are saved to the 
# 'FixedCompositionSearch' table. You can view progress in the Web UI.
if state.is_completed():
    print("Search completed!")
else:
    print("Search is still running or was interrupted.")
```
