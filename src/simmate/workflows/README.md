# Simmate Workflows

This module brings together all predefined workflows and organizes them by application for convenience.

This module covers basic use, but more information is available in `simmate.workflow_engine.workflow`.


# Basic use

[Tutorials 01-05](https://github.com/jacksund/simmate/tree/main/tutorials) will teach you how to run workflows and access their results. But as a review:

``` python
from simmate.workflows.static_energy import StaticEnergy__Vasp__Matproj as workflow

# runs the workflow and returns a state
state = workflow.run(structure="my_structure.cif")
result = state.result()

# gives the DatabaseTable where ALL results are stored
workflow.database_table  # --> gives all relaxation results
workflow.all_results  # --> gives all results for this relaxation preset
df = workflow.all_results.to_dataframe()  # convert to pandas dataframe
```

Further information on interacting with workflows can be found in the `simmate.workflow_engine` module as well -- particularly, the `simmate.workflow_engine.workflow` module.


# Avoiding long import paths

If you are a regular python user, you'll notice the import path above is long and unfriendly. If you'd like to avoid importing this way, you can instead use the `get_workflow` utility:

``` python
from simmate.workflows.utilities import get_workflow

workflow = get_workflow("static-energy.vasp.matproj")
```


# Workflow naming conventions

All workflow names follow a specific format of `Type__Calculator__Preset` so for an example workflow like `StaticEnergy__Vasp__Matproj` this means that...

- Type = StaticEnergy (workflow runs a single point energy)
- Calculator = Vasp  (workflow uses VASP to calculate the energy)
- Preset = Matproj  (workflow uses "Matproj" type settings in the calculation)

The workflow name can also be used to infer where the workflow is located in python. For `StaticEnergy__Vasp__Matproj`, this corresponds to a name of `static-energy.vasp.matproj` and means the workflow can be accessed in the following ways:

1. `from simmate.workflows.static_energy import StaticEnergy__Vasp__Matproj` (uses the `type`)
2. `from simmate.calculators.vasp.workflows.static_energy.all import StaticEnergy__Vasp__Matproj`  (uses the `type` and `calculator`)
3. `from simmate.calculators.vasp.workflows.static_energy.matproj import StaticEnergy__Vasp__Matproj`  (uses the `type` and `calculator` and `preset`)

These imports all give the same workflow, but we recommend stick to the first option because it is the most convienent and easiest to remember. The only reason you'll need to interact with the other options is to either:

1. Find the source code for a workflow (see section below for more)
2. Optimize the speed of your imports (advanced users only)


<!--
# Location of a workflow in the website interface

You can follow the naming conventions (described above) to find a workflow in the website interface:

```
# Template to use for finding workflows
https://simmate.org/workflows/{TYPE}/{CALCULATOR}/{PRESET}

# Example with StaticEnergy__Vasp__Matproj
https://simmate.org/workflows/static-energy/vasp/matproj
```
-->


# Location of a workflow's source code

The code that defines these workflows and configures their settings are located in the corresponding `simmate.calculators` module. We make workflows accessible here because users often want to search for workflows by application -- not by their calculator name. The source code of a workflow can be found using the naming convention for workflows described above:

``` python
# Template to use for finding workflows
from simmate.calculators.{CALCULATOR}.workflows.{TYPE}.{PRESET} import {FULL_NAME}

# Example with StaticEnergy__Vasp__Matproj
from simmate.calculators.vasp.workflows.static_energy.matproj import StaticEnergy__Vasp__Matproj
```

# Parameters

Knowing which parameters are available and how to use them is essential to use Simmate to the fullest. We therefore outline ALL unique parameters for ALL workflows here.

To see which parameters are allow for a given workflow, you can use the `simmate explore` command to list them. Alternatively, in python, you can use `workflow.show_parameters()`.

For example:

```
workflow.show_parameters()

- command
- compress_output
- directory
- is_restart
- pre_sanitize_structure
- pre_standardize_structure
- run_id
- source
- structure
```

You can then search for these parameters below to learn more about them.


## command
The command that will be called during execution of a program. There is typically a default set for this that you only need to change unless you'd like parallelization. For example, VASP workflows use `vasp_std > vasp.out` by default but you can override this to use `mpirun`.
``` python
# python example
command="mpirun -n 8 vasp_std > vasp.out"
```
``` yaml
# yaml file example
command: mpirun -n 8 vasp_std > vasp.out
```


## composition
The composition input can be anything compatible with the `Composition` toolkit class. Note that compositions are sensitive to atom counts / multiplicity. There is a difference between giving `Ca2N` and `Ca4N2` in several workflows. Accepted inputs include:

- a string (recommended)
``` python
# python example
composition="Ca2NF"
```
``` yaml
# yaml file example
composition: Ca2NF
```

- a dictionary that gives the composition
``` python
# python example
composition={"Ca": 2, "N": 1, "F": 1}
```
``` yaml
# yaml file example
composition:
    Ca: 2
    N: 1
    F: 1
```

- a `Composition` object (best for advanced logic)
``` python
# python example
from simmate.toolkit import Compositon

composition = Composition("Ca2NF")
```

- json/dictionary serialization from pymatgen


## compress_output
Whether to compress the `directory` to a zip file at the end of the run. After compression, it will also delete the directory. The default is False.
``` python
# python example
compress_output=True
```
``` yaml
# yaml file example
command: true
```


## copy_previous_directory
Whether to copy the directory from the previous calculation (if there is one) and then use it as a starting point for this new calculation. This is only possible if you provided an input that points to a previous calculation. For example, `structure` would need to use a database-like input:
``` python
# python example
structure = {"database_table": "Relaxation", "database_id": 123}
copy_previous_directory=True
```
``` yaml
# yaml file example
structure:
    database_table: Relaxation
    database_id: 123
copy_previous_directory: true
```

The default is `False`, and it is not recommended to use this in existing workflows. Nested workflows that benefit from this feature use it automatically.


## diffusion_analysis_id
(advanced users only) The entry id from the `DiffusionAnalysis` table to link the results to. This is set automatically by higher-level workflows and rarely (if ever) set by the user.


## directory
The directory to run everything in -- either as a relative or full path. This is passed to the ulitities function `simmate.ulitities.get_directory`, which generates a unique foldername if not provided (such as `simmate-task-12390u243`). This will be converted into a `pathlib.Path` object. Accepted inputs include:

- leave as default (recommended)

- a string
``` python
# python example
directory = "my-new-folder-00"
```
``` yaml
# yaml file example
directory: my-new-folder-00
```

- a `pathlib.Path` (best for advanced logic)

``` python
# python example
from pathlib import Path

directory = Path("my-new-folder-00")
```


## directory_new
Unique to the `restart.simmate.automatic` workflow, this is the folder that the workflow will be continued in. Follows the same rules/inputs as the `directory` parameter.


## directory_old
Unique to the `restart.simmate.automatic` workflow, this is the original folder that should be used at the starting point. Follows the same rules/inputs as the `directory` parameter.


## fitness_field
(advanced users only) For evolutionary searches, this is the value that should be optimized. Specifically, it should minimized this value (lower value = better fitness). The default is `energy_per_atom`, but you may want to set this to a custom column in a custom database table.


## input_parameters
(experimental feature) Unique to `customized.vasp.user-config`. This is a list of parameters to pass to `workflow_base`.


## is_restart
(experimental feature) Whether the calculation is a restarted workflow run. Default is False. If set to true, the workflow will go through the given directory (which must be provided) and see where to pick up.
``` python
# python example
directory = "my-old-calc-folder"
is_restart = True
```
``` yaml
# yaml file example
directory: my-old-calc-folder
is_restart: true
```


## limit_best_survival
For evolutionary searches, fixed compositions will be stopped when the best individual remains unbeaten for this number of new individuals. The default is typically set based on the number of atoms in the composition.
``` python
# python example
limit_best_survival = 100
```
``` yaml
# yaml file example
limit_best_survival: 100
```

## max_atoms
For workflows that involve generating a supercell or random structure, this will be the maximum number of sites to allow in the generate structure(s). For example, NEB workflows would set this value to something like 100 atoms to limit their supercell image sizes. Alternatively, a evolutionary search may set this to 10 atoms to limit the compositions & stoichiometries that are explored.
``` python
# python example
max_atoms = 100
```
``` yaml
# yaml file example
max_atoms: 100
```

## max_structures

## migrating_specie

## migration_hop

## migration_hop_id

## migration_images


## min_atoms
This is the opposite of `max_atoms` as this will be the minimum number of sites to allow in the generate structure(s). See `max_atoms` for details.


## min_length

## nfirst_generation

## nimages

## nsteadystate

## nsteps

## pre_sanitize_structure

## pre_standardize_structure

## run_id

## search_id

## selector_kwargs

## selector_name

## singleshot_sources

## sleep_step

## source

## steadystate_sources

## structure

## structure_source_id

## subworkflow_kwargs

## subworkflow_name

## supercell_end

## supercell_start

## tags

## temperature_end

## temperature_start

## time_step

## updated_settings

## validator_kwargs

## validator_name

## workflow_base
