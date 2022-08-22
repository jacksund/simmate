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

To see which parameters are allow for a given workflow, you can use the explore command to list them:

``` bash
simmate workflows explore
```


Alternatively, in python, you can use `workflow.show_parameters()`. For example:

```
workflow.show_parameters()

- angle_tolerance
- command
- compress_output
- directory
- is_restart
- run_id
- source
- standardize_structure
- structure
- symmetry_precision
```

You can then search for these parameters below to learn more about them.


## angle_tolerance
If standardize_structure=True, then this is the cutoff value used to determine
if the angles between sites are symmetrically equivalent. (in Degrees)
``` python
# python example
angle_tolerance = 10.0
```
``` yaml
# yaml file example
angle_tolerance: 10.0
```


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

## convergence_limit
For evolutionary searches, the search will be considered converged when the best structure is not changing by this amount (in eV). In order to officially signal the end of the search, the best structure must survive within this convergence limit for a specific number of new individuals -- this is controlled by the `limit_best_survival`. The default of 1meV is typically sufficient and does not need to be changed. More often, users should update `limit_best_survival` instead.
``` python
# python example
convergence_limit = 0.005
```
``` yaml
# yaml file example
convergence_limit: 0.005
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
(advanced users only)
For evolutionary searches, this is the value that should be optimized. Specifically, it should minimized this value (lower value = better fitness). The default is `energy_per_atom`, but you may want to set this to a custom column in a custom database table.


## input_parameters
(experimental feature)
Unique to `customized.vasp.user-config`. This is a list of parameters to pass to `workflow_base`.


## is_restart
(experimental feature)
Whether the calculation is a restarted workflow run. Default is False. If set to true, the workflow will go through the given directory (which must be provided) and see where to pick up.
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
For evolutionary searches, fixed compositions will be stopped when the best individual remains unbeaten for this number of new individuals. In order to absorb similar structures (e.g. identical structures but with minor energy differences), structures within the `convergence_limit` parameter (e.g. +1meV) are not considered when counting historical structures. This helps to prevent the search from continuing in cases where the search is likely already converged but making <0.1meV improvements. The default is typically set based on the number of atoms in the composition.
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
For workflows that generate new structures (and potentially run calculations on them), this will be the maximum number of structures allowed. The workflow will end at this number of structures regardless of whether the calculation/search is converged or not.
``` python
# python example
max_structures = 100
```
``` yaml
# yaml file example
max_structures: 100
```

## migrating_specie
This is the atomic species/element that will be moving in the analysis (typically NEB or MD diffusion calculations). Note, oxidation states (e.g. "Ca2+") can be used, but this requires your input structure to be oxidation-state decorated as well.
``` python
# python example
migrating_specie = "Li"
```
``` yaml
# yaml file example
migrating_specie: Li
```


## migration_hop
(advanced users only)
The atomic path that should be analyzed. Inputs are anything compatible with the `MigrationHop` class of the `simmate.toolkit.diffusion` module. This includes:

- `MigrationHop` object
- a database entry in the `MigrationHop` table

(TODO: if you'd like full examples, please ask our team to add them)


## migration_hop_id
(advanced users only) The entry id from the `MigrationHop` table to link the results to. This is set automatically by higher-level workflows and rarely (if ever) set by the user. If used, you'll likely need to set `diffusion_analysis_id` as well.


## migration_images
The full set of images (including endpoint images) that should be analyzed. Inputs are anything compatible with the `MigrationImages` class of the `simmate.toolkit.diffusion` module, which is effectively a list of `structure` inputs. This includes:

- `MigrationImages` object

- a list of `Structure` objects

- a list of filenames (cif or POSCAR)
``` python
# python example
migration_images = [
    "image_01.cif",
    "image_02.cif",
    "image_03.cif",
    "image_04.cif",
    "image_05.cif",
]
```
``` yaml
# yaml file example
migration_images:
    - image_01.cif
    - image_02.cif
    - image_03.cif
    - image_04.cif
    - image_05.cif
```



## min_atoms
This is the opposite of `max_atoms` as this will be the minimum number of sites to allow in the generate structure(s). See `max_atoms` for details.


## min_length
When generating a supercell, this is the minimum length for each lattice vector of the generate cell (in Angstroms).
``` python
# python example
min_length = 7.5
```
``` yaml
# yaml file example
min_length: 7.5
```

## nfirst_generation
For evolutionary searches, no mutations or "child" individuals will be scheduled until this
number of individuals have been calculated. This ensures we have a good pool of candidates calculated before we start selecting parents and mutating them.
``` python
# python example
nfirst_generation = 15
```
``` yaml
# yaml file example
nfirst_generation: 15
```

## nimages
The number of images (or structures) to use in the analysis. This does NOT include the endpoint images (start/end structures). More is better, but computationally expensive. We recommend keeping this value odd in order to ensure there is an image at the midpoint.
``` python
# python example
nimages = 5
```
``` yaml
# yaml file example
nimages: 5
```
WARNING: For calculators such as VASP, your `command` parameter must use a number of cores that is divisible by `nimages`. For example, `nimages=3` and `command="mpirun -n 10 vasp_std > vasp.out"` will fail because 10 is not divisible by 3.


## nsteadystate
The number of individual workflows to have scheduled at once. This therefore sets the queue size of an evolutionary search. Note, the number of workflows ran in parallel is determined by the number of `Workers` started (i.e. starting 3 workers will run 3 workflows in parallel, even if 100 workflows are in the queue). The steady-state does, however, set the **maximum** number of parallel runs because the queue size will never exceed the `nsteadystate` value. This parameter is closely tied with `steadystate_sources`, so be sure to read about that parameter as well.
``` python
# python example
nsteadystate = 50
```
``` yaml
# yaml file example
nsteadystate: 50
```

## nsteps
The total number of steps to run the calculation on. For example, in molecular dynamics workflows, this will stop the simulation after this many steps.
``` python
# python example
nsteps = 10000
```
``` yaml
# yaml file example
nsteps: 10000
```


## run_id
The id assigned to a specific workflow run / calculation. If not provided this will be randomly generated, and we highly recommended leaving this at the default value. Note, this is based on unique-ids (UUID), so every id should be 100% unique and in a string format.
``` python
# python example
run_id = "my-unique-id-123"
```
``` yaml
# yaml file example
run_id: my-unique-id-123
```

## search_id
(advanced users only)
The evolutionary search that this individual is associated with. This allows us to determine which `Selector`, `Validator`, and `StopCondition` should be used when creating and evaluating the individual. When running a search, this is set automatically when submitting a new flow.


## selector_kwargs
(advanced users only)
Extra conditions to use when initializing the selector class. `MySelector(**selector_kwargs)`. The input should be given as a dictionary. Note, for evolutionary searches, the composition kwarg is added automatically. This is closely tied with the `selector_name` parameter so be sure to read that section as well.


## selector_name
(experimental feature; advanced users only)
The base selector class that should be used. The class will be initialized using `MySelector(**selector_kwargs)`. The input should be given as a string.

WARNING: Currently, we only support truncated selection, so this should be left at its default value.


## singleshot_sources
(experimental feature; advanced users only)
A list of structure sources that run once and never again. This includes generating input structures from known structures (from third-party databases), prototypes, or substituiting known structures.

In the current version of simmate, these features are not enabled and this input should be ignored.


## sleep_step
When there is a cycle within a workflow (such as iteratively checking the number of subworkflows submitted and updating results), this is the amount of time in seconds that the workflow will shutdown before restarting the cycle. For evolutionary searches, setting this to a larger value will save on computation resources and database load, so we recommend increasing it where possible.
``` python
# python example
sleep_step = 180  # 3 minutes
```
``` yaml
# yaml file example
run_id: 180
```

## source
(experimental feature; advanced users only)
This column indicates where the input data (and other parameters) came from. The source could be a number of things including...
 - a third party id
 - a structure from a different Simmate datbase table
 - a transformation of another structure
 - a creation method
 - a custom submission by the user

By default, this is a dictionary to account for the many different scenarios. Here are some examples of values used in this column:

``` python
# from a thirdparty database or separate table
source = {
    "database_table": "MatprojStructure",
    "database_id": "mp-123",
}

# from a random structure creator
source = {"creator": "PyXtalStructure"}

# from a templated structure creator (e.g. substituition or prototypes)
source = {
    "creator": "PrototypeStructure",
    "database_table": "AFLOWPrototypes",
    "id": 123,
}

# from a transformation
source = {
    "transformation": "MirrorMutation",
    "database_table":"MatprojStructure",
    "parent_ids": ["mp-12", "mp-34"],
}
```

Typically, the `source` is set automatically, and users do not need to update it.


## standardize_structure
In some cases, we may want to standardize the structure during our setup().

This means running symmetry analysis on the structure in order to reduce the symmetry and also convert it to some standardized form. There are three different forms to choose from and thus 3 different values that `standardize_structure` can be set to:

- `primitive`: for the standard primitive unitcell
- `conventional`: for the standard conventional unitcell
- `primitive-LLL`: for the standard primitive unitcell that is then LLL-reduced
- `False`: this is the default and will disable this feature

We recommend using `primitive-LLL` when the smallest possible and most cubic unitcell is desired.

We recommend using `primitive` when calculating band structures and ensuring we have a standardized high-symmetry path. Note,Existing band-structure workflows use this automatically.

To control the tolerances used to symmetrize the structure, you can use the symmetry_precision and angle_tolerance attributes.

By default, no standardization is applied.

``` python
# python example
standardize_structure = "primitive-LLL"
```
``` yaml
# yaml file example
standardize_structure: primitive-LLL
```


## steadystate_sources
(experimental feature; advanced users only)
The sources that will be scheduled at a "steady-state", meaning there will always be a set number of individuals scheduled/running for this type of structure source. This should be defined as a dictionary where each is `{"source_name": percent}`. The percent determines the number of steady stage calculations that will be running for this at any given time. It will be a percent of the `nsteadystate` parameter, which sets the total number of individuals to be scheduled/running. For example, if `nsteadystate=40` and we add a source of `{"RandomSymStructure": 0.30, ...}`, this means 0.25*40=10 randomly-created individuals will be running/submitted at all times. The source can be from either the `toolkit.creator` or `toolkit.transformations` modules.
``` python
# python example
singleshot_sources = {
    "RandomSymStructure": 0.30,
    "from_ase.Heredity": 0.30,
    "from_ase.SoftMutation": 0.10,
    "from_ase.MirrorMutation": 0.10,
    "from_ase.LatticeStrain": 0.05,
    "from_ase.RotationalMutation": 0.05,
    "from_ase.AtomicPermutation": 0.05,
    "from_ase.CoordinatePerturbation": 0.05,
}
```
``` yaml
# yaml file example
singleshot_sources:
    RandomSymStructure: 0.30
    from_ase.Heredity: 0.30
    from_ase.SoftMutation: 0.10
    from_ase.MirrorMutation: 0.10
    from_ase.LatticeStrain: 0.05
    from_ase.RotationalMutation: 0.05
    from_ase.AtomicPermutation: 0.05
    from_ase.CoordinatePerturbation: 0.05
```

Note: if your percent values do not sum to 1, they will be rescaled. When calculating `percent*nsteadystate`, the value will be rounded to the nearest integer.

We are moving towards allowing kwargs or class objects as well, but this is not yet allowed. For example, anything other than `percent` would be treated as a kwarg:
``` yaml
singleshot_sources:
    RandomSymStructure:
        percent: 0.30
        spacegroups_exclude:
            - 1
            - 2
            - 3
        site_generation_method: MyCustomMethod
```


## structure
The crystal structure to be used for the analysis. The input can be anything compatible with the `Structure` toolkit class. Accepted inputs include:

- a filename (cif or poscar) (recommended)
``` python
# python example
structure="NaCl.cif"
```
``` yaml
# yaml file example
structure: NaCl.cif
```

- a dictionary that points to a database entry. Note, instead of `database_id`, you can also use the `run_id` or `directory` to indicate which entry to load. Further, if the database table is linked to multiple structures (e.g. relaxations have a `structure_start` and `structure_final`), then you can also add the `structure_field` to specify which to choose. 
``` python
# python examples

# example 1
structure={
    "database_table": "MatprojStructure",
    "database_id": "mp-123",
}

# example 2
structure={
    "database_table": "StaticEnergy",
    "database_id": 50,
}

# example 3
structure={
    "database_table": "Relaxation",
    "database_id": 50,
    "structure_field": "structure_final",
}
```
``` yaml
# yaml file example
structure:
    database_table: MatprojStructure
    database_id: mp-123
```

- a `Structure` object (best for advanced logic)
``` python
# python example
from simmate.toolkit import Structure

structure = Structure(
    lattice=[
        [2.846, 2.846, 0.000],
        [2.846, 0.000, 2.846],
        [0.000, 2.846, 2.846],
    ],
    species=["Na", "Cl"],
    coords=[
        [0.5, 0.5, 0.5],
        [0.0, 0.0, 0.0],
    ],
    coords_are_cartesian=False,
)
```

- json/dictionary serialization from pymatgen


## structure_source_id
(advanced users only)
The structure source that this individual is associated with. This allows us to determine how the new individual should be created. When running a search, this is set automatically when submitting a new flow.

## subworkflow_kwargs
Make sure you read about `subworkflow_name` parameter first. This is a dictionary of parameters to pass to each subworkflow run. For example, the workflow will be ran as `subworkflow.run(**subworkflow_kwargs)`. Note, many workflows that use this argument will automatically pass information that is unique to each call (such as `structure`).
``` python
# python example
subworkflow_kwargs=dict(
    command="mpirun -n 4 vasp_std > vasp.out",
    compress_output=True,
)
```
``` yaml
# yaml file example
subworkflow_kwargs:
    command: mpirun -n 4 vasp_std > vasp.out
    compress_output: True
```

## subworkflow_name
The name of workflow that used to evaluate structures generated. For example, in evolutionary searches, individuals are created and then relaxed using the `relaxation.vasp.staged` workflow. Any workflow that is registered and accessible via the `get_workflow` utility can be used instead. (note: in the future we will allow unregisterd flows as well). If you wish to submit extra arguments to each workflow run, you can use the `subworkflow_kwargs` parameter.
``` python
# python example
subworkflow_name = "relaxation.vasp.staged"
```
``` yaml
# yaml file example
subworkflow_name: relaxation.vasp.staged
```


## supercell_end
The endpoint image supercell to use. This is really just a `structure` parameter under a different name, so everything about the `structure` parameter also applies here.


## supercell_start
The starting image supercell to use. This is really just a `structure` parameter under a different name, so everything about the `structure` parameter also applies here.


## symmetry_precision
If standardize_structure=True, then this is the cutoff value used to determine
if the sites are symmetrically equivalent. (in Angstroms)
``` python
# python example
symmetry_precision = 0.1
```
``` yaml
# yaml file example
symmetry_precision: 0.1
```


## tags
When submitting workflows via the `run_cloud` command, tags are 'labels' that help control which workers are allowed to pick up and run the submitted workflow. Workers should be started with matching tags in order for these scheduled flows to run.
``` python
# python example
tags = ["my-tag-01", "my-tag-02"]
```
``` yaml
# yaml file example
tags:
    - my-tag-01
    - my-tag-02
```


## temperature_end
For molecular dynamics simulations, this is the temperature to end the simulation at (in Kelvin). This temperatue will be reached through a linear transition from the `temperature_start` parameter.
``` python
# python example
temperature_end = 1000
```
``` yaml
# yaml file example
temperature_end: 1000
```


## temperature_start
For molecular dynamics simulations, this is the temperature to begin the simulation at (in Kelvin).
``` python
# python example
temperature_start = 250
```
``` yaml
# yaml file example
temperature_start: 250
```


## time_step
For molecular dynamics simulations, this is time time between each ionic step (in femtoseconds).
``` python
# python example
time_step = 1.5
```
``` yaml
# yaml file example
time_step: 1.5
```


## updated_settings
(experimental feature)
Unique to `customized.vasp.user-config`. This is a list of parameters to update the `workflow_base` with. This often involves updating the base class attributes.


## validator_kwargs
(advanced users only)
Extra conditions to use when initializing the validator class. `MyValidator(**validator_kwargs)`. The input should be given as a dictionary. Note, for evolutionary searches, the composition kwarg is added automatically. This is closely tied with the `validator_name` parameter so be sure to read that section as well.


## validator_name
(experimental feature; advanced users only)
The base validator class that should be used. The class will be initialized using `MyValidator(**validator_kwargs)`. The input should be given as a string.

WARNING: Currently, we only support `CrystallNNFingerprint` validation, so this should be left at its default value.


## workflow_base
(experimental feature)
Unique to `customized.vasp.user-config`. This is the base workflow to use when updating critical settings.
