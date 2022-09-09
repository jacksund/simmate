# Parameters

## Overview

Knowing which parameters are available and how to use them is essential. We therefore outline **all** unique parameters for **all** workflows here.

To see which parameters are allowed for a given workflow, you can use the `explore` command or `workflow.show_parameters()`:

=== "command line"
    ``` bash
    simmate workflows explore
    ```

=== "python"

    ``` python
    workflow.show_parameters()
    ```

If you need more details on a parameter or would like to request a new one, just let us know!


You can then search for these parameters below to learn more about them.


--------------------------


## angle_tolerance
If standardize_structure=True, then this is the cutoff value used to determine
if the angles between sites are symmetrically equivalent. (in Degrees)

=== "yaml"
    ``` yaml
    angle_tolerance: 10.0
    ```
=== "toml"
    ``` toml
    angle_tolerance = 10.0
    ```
=== "python"
    ``` python
    angle_tolerance = 10.0
    ```

--------------------------

## best_survival_cutoff
For evolutionary searches, fixed compositions will be stopped when the best individual remains unbeaten for this number of new individuals. In order to absorb similar structures (e.g. identical structures but with minor energy differences), structures within the `convergence_cutoff` parameter (e.g. +1meV) are not considered when counting historical structures. This helps to prevent the search from continuing in cases where the search is likely already converged but making <0.1meV improvements. The default is typically set based on the number of atoms in the composition.

=== "yaml"
    ``` yaml
    best_survival_cutoff: 100
    ```
=== "toml"
    ``` toml
    best_survival_cutoff = 100
    ```
=== "python"
    ``` python
    best_survival_cutoff = 100
    ```

--------------------------

## chemical_system
The chemical system to be used in the analysis. This should be given as a string
and in the format `Element1-Element2-Element3-...`. For example, `Na-Cl`, `Y-C`,
and `Y-C-F` are valid chemical systems.

=== "yaml"
    ``` yaml
    chemical_system: Na-Cl
    ```
=== "toml"
    ``` yaml
    chemical_system = "Na-Cl"
    ```
=== "python"
    ``` python
    chemical_system = "Na-Cl"
    ```

!!! warning
    Some workflows only accept a chemical system with a specific number of elements.
    An example of this is the `structure-prediction.python.binary-composition` search
    which only allows two elements (e.g. `Y-C-F` would raise an error)

--------------------------

## command
The command that will be called during execution of a program. There is typically a default set for this that you only need to change unless you'd like parallelization. For example, VASP workflows use `vasp_std > vasp.out` by default but you can override this to use `mpirun`.

=== "yaml"
    ``` yaml
    command: mpirun -n 8 vasp_std > vasp.out
    ```
=== "toml"
    ``` toml
    command = "mpirun -n 8 vasp_std > vasp.out"
    ```
=== "python"
    ``` python
    command = "mpirun -n 8 vasp_std > vasp.out"
    ```

<!-- NOTES ON SUBCOMMANDS (feature is currently disabled)

command list expects three subcommands:
  command_bulk, command_supercell, and command_neb

I separate these out because each calculation is a very different scale.
For example, you may want to run the bulk relaxation on 10 cores, the
supercell on 50, and the NEB on 200. Even though more cores are available,
running smaller calculation on more cores could slow down the calc.
["command_bulk", "command_supercell", "command_neb"]


If you are running this workflow via the command-line, you can run this
with...

``` bash
simmate workflows run diffusion/all-paths -s example.cif -c "cmd1; cmd2; cmd3"
```
Note, the `-c` here is very important! Here we are passing three commands
separated by semicolons. Each command is passed to a specific workflow call:
    - cmd1 --> used for bulk crystal relaxation and static energy
    - cmd2 --> used for endpoint supercell relaxations
    - cmd3 --> used for NEB
Thus, you can scale your resources for each step. Here's a full -c option:
-c "vasp_std > vasp.out; mpirun -n 12 vasp_std > vasp.out; mpirun -n 70 vasp_std > vasp.out"
-->

--------------------------

## composition
The composition input can be anything compatible with the `Composition` toolkit class. Note that compositions are sensitive to atom counts / multiplicity. There is a difference between giving `Ca2N` and `Ca4N2` in several workflows. Accepted inputs include:

**a string (recommended)**

=== "yaml"
    ``` yaml
    composition: Ca2NF
    ```
=== "toml"
    ``` toml
    composition = "Ca2NF"
    ```
=== "python"
    ``` python
    composition = "Ca2NF"
    ```

**a dictionary that gives the composition**

=== "yaml"
    ``` yaml
    composition:
        Ca: 2
        N: 1
        F: 1
    ```
=== "toml"
    ``` yaml
    [composition]
    Ca = 2
    N = 1
    F = 1
    ```
=== "python"
    ``` python
    composition={
        "Ca": 2, 
        "N": 1, 
        "F": 1,
    }
    ```

**a `Composition` object (best for advanced logic)**

=== "python"
    ``` python
    from simmate.toolkit import Compositon
    
    composition = Composition("Ca2NF")
    ```

**json/dictionary serialization from pymatgen**


--------------------------

## compress_output
Whether to compress the `directory` to a zip file at the end of the run. After compression, it will also delete the directory. The default is False.

=== "yaml"
    ``` yaml
    compress_output: true
    ```
=== "toml"
    ``` toml
    compress_output = true
    ```
=== "python"
    ``` python
    compress_output = True
    ```

--------------------------

## convergence_cutoff
For evolutionary searches, the search will be considered converged when the best structure is not changing by this amount (in eV). In order to officially signal the end of the search, the best structure must survive within this convergence limit for a specific number of new individuals -- this is controlled by the `best_survival_cutoff`. The default of 1meV is typically sufficient and does not need to be changed. More often, users should update `best_survival_cutoff` instead.

=== "yaml"
    ``` yaml
    convergence_cutoff: 0.005
    ```
=== "toml"
    ``` toml
    convergence_cutoff = 0.005
    ```
=== "python"
    ``` python
    convergence_cutoff = 0.005
    ```

--------------------------

## copy_previous_directory
Whether to copy the directory from the previous calculation (if there is one) and then use it as a starting point for this new calculation. This is only possible if you provided an input that points to a previous calculation. For example, `structure` would need to use a database-like input:

=== "yaml"
    ``` yaml
    structure:
        database_table: Relaxation
        database_id: 123
    copy_previous_directory: true
    ```
=== "toml"
    ``` toml
    copy_previous_directory: true

    [structure]
    database_table = "Relaxation"
    database_id = 123
    ```
=== "python"
    ``` python
    structure = {"database_table": "Relaxation", "database_id": 123}
    copy_previous_directory=True
    ```


The default is `False`, and it is not recommended to use this in existing workflows. Nested workflows that benefit from this feature use it automatically.

--------------------------

## diffusion_analysis_id
(advanced users only) The entry id from the `DiffusionAnalysis` table to link the results to. This is set automatically by higher-level workflows and rarely (if ever) set by the user.

--------------------------

## directory
The directory to run everything in -- either as a relative or full path. This is passed to the ulitities function `simmate.ulitities.get_directory`, which generates a unique foldername if not provided (such as `simmate-task-12390u243`). This will be converted into a `pathlib.Path` object. Accepted inputs include:

**leave as default (recommended)**

**a string**

=== "yaml"
    ``` yaml
    directory: my-new-folder-00
    ```
=== "toml"
    ``` toml
    directory = "my-new-folder-00"
    ```
=== "python"
    ``` python
    directory = "my-new-folder-00"
    ```


**a `pathlib.Path` (best for advanced logic)**

=== "python"
    ``` python
    from pathlib import Path
    
    directory = Path("my-new-folder-00")
    ```

--------------------------

## directory_new
Unique to the `restart.simmate.automatic` workflow, this is the folder that the workflow will be continued in. Follows the same rules/inputs as the `directory` parameter.

--------------------------

## directory_old
Unique to the `restart.simmate.automatic` workflow, this is the original folder that should be used at the starting point. Follows the same rules/inputs as the `directory` parameter.

--------------------------

## fitness_field
(advanced users only)
For evolutionary searches, this is the value that should be optimized. Specifically, it should minimized this value (lower value = better fitness). The default is `energy_per_atom`, but you may want to set this to a custom column in a custom database table.

--------------------------

## input_parameters
(experimental feature)
Unique to `customized.vasp.user-config`. This is a list of parameters to pass to `workflow_base`.

--------------------------

## is_restart
(experimental feature)
Whether the calculation is a restarted workflow run. Default is False. If set to true, the workflow will go through the given directory (which must be provided) and see where to pick up.

=== "yaml"
    ``` yaml
    directory: my-old-calc-folder
    is_restart: true
    ```
=== "toml"
    ``` toml
    directory = "my-old-calc-folder"
    is_restart = true
    ```
=== "python"
    ``` python
    directory = "my-old-calc-folder"
    is_restart = True
    ```

--------------------------

## max_atoms
For workflows that involve generating a supercell or random structure, this will be the maximum number of sites to allow in the generated structure(s). For example, an evolutionary search may set this to 10 atoms to limit the compositions & stoichiometries that are explored.

=== "yaml"
    ``` yaml
    max_atoms: 10
    ```
=== "toml"
    ``` toml
    max_atoms = 10
    ```
=== "python"
    ``` python
    max_atoms = 10
    ```

--------------------------

## max_path_length
For diffusion workflows, this the maximum length allowed for a single path.

=== "yaml"
    ``` yaml
    max_path_length: 3.5
    ```
=== "toml"
    ``` toml
    max_path_length = 3.5
    ```
=== "python"
    ``` python
    max_path_length = 3.5
    ```

--------------------------

## max_stoich_factor
The maximum stoichiometric ratio that will be analyzed. In a binary
system evolutionary search, this only look at non-reduced compositions up to the max_stoich_factor. For example, this means Ca2N and max factor of 4 would only 
look up to Ca8N4 and skip any compositions with more atoms (e.g. Ca10N5 is skipped)

=== "yaml"
    ``` yaml
    max_stoich_factor: 5
    ```
=== "toml"
    ``` toml
    max_stoich_factor = 5
    ```
=== "python"
    ``` python
    max_stoich_factor = 5
    ```

--------------------------

## max_structures
For workflows that generate new structures (and potentially run calculations on them), this will be the maximum number of structures allowed. The workflow will end at this number of structures regardless of whether the calculation/search is converged or not.

=== "yaml"
    ``` yaml
    max_structures: 100
    ```
=== "toml"
    ``` toml
    max_structures = 100
    ```
=== "python"
    ``` python
    max_structures = 100
    ```

!!! warning
    In `structure-prediction` workflows, `min_structure_exact` takes priority 
    over this setting, so it is possible for your search to exceed your 
    maximum number of structures. If you want `max_structures` to have absolute
    control, you can set `min_structure_exact` to 0.

--------------------------

## max_supercell_atoms
For workflows that involve generating a supercell, this will be the maximum number of sites to allow in the generated structure(s). For example, NEB workflows would set this value to something like 100 atoms to limit their supercell image sizes.

=== "yaml"
    ``` yaml
    max_supercell_atoms: 100
    ```
=== "toml"
    ``` toml
    max_supercell_atoms = 100
    ```
=== "python"
    ``` python
    max_supercell_atoms = 100
    ```

--------------------------

## migrating_specie
This is the atomic species/element that will be moving in the analysis (typically NEB or MD diffusion calculations). Note, oxidation states (e.g. "Ca2+") can be used, but this requires your input structure to be oxidation-state decorated as well.

=== "yaml"
    ``` yaml
    migrating_specie: Li
    ```
=== "toml"
    ``` toml
    migrating_specie = "Li"
    ```
=== "python"
    ``` python
    migrating_specie = "Li"
    ```

--------------------------

## migration_hop
(advanced users only)
The atomic path that should be analyzed. Inputs are anything compatible with the `MigrationHop` class of the `simmate.toolkit.diffusion` module. This includes:

- `MigrationHop` object
- a database entry in the `MigrationHop` table

(TODO: if you'd like full examples, please ask our team to add them)

--------------------------

## migration_images
The full set of images (including endpoint images) that should be analyzed. Inputs are anything compatible with the `MigrationImages` class of the `simmate.toolkit.diffusion` module, which is effectively a list of `structure` inputs. This includes:

**`MigrationImages` object**

**a list of `Structure` objects**

**a list of filenames (cif or POSCAR)**

=== "yaml"
    ``` yaml
    migration_images:
        - image_01.cif
        - image_02.cif
        - image_03.cif
        - image_04.cif
        - image_05.cif
    ```
=== "toml"
    ``` toml
    migration_images = [
        "image_01.cif",
        "image_02.cif",
        "image_03.cif",
        "image_04.cif",
        "image_05.cif",
    ]
    ```
=== "python"
    ``` python
    migration_images = [
        "image_01.cif",
        "image_02.cif",
        "image_03.cif",
        "image_04.cif",
        "image_05.cif",
    ]
    ```

--------------------------

## min_atoms
This is the opposite of `max_atoms` as this will be the minimum number of sites allowed in the generate structure(s). See `max_atoms` for details.

--------------------------

## min_structures_exact

(experimental) The minimum number of structures that must be calculated with exactly
matching nsites as specified in the fixed-composition.

--------------------------

## min_supercell_atoms

This is the opposite of `max_supercell_atoms` as this will be the minimum number of sites allowed in the generated supercell structure.

--------------------------

## min_supercell_vector_lengths

When generating a supercell, this is the minimum length for each lattice vector of the generated cell (in Angstroms). For workflows such as NEB, larger is better but more computationally expensive.

=== "yaml"
    ``` yaml
    min_supercell_vector_lengths: 7.5
    ```
=== "toml"
    ``` toml
    min_supercell_vector_lengths = 7.5
    ```
=== "python"
    ``` python
    min_supercell_vector_lengths = 7.5
    ```

--------------------------

## nfirst_generation
For evolutionary searches, no mutations or "child" individuals will be scheduled until this
number of individuals have been calculated. This ensures we have a good pool of candidates calculated before we start selecting parents and mutating them.

=== "yaml"
    ``` yaml
    nfirst_generation: 15
    ```
=== "toml"
    ``` toml
    nfirst_generation = 15
    ```
=== "python"
    ``` python
    nfirst_generation = 15
    ```

--------------------------

## nimages
The number of images (or structures) to use in the analysis. This does NOT include the endpoint images (start/end structures). More is better, but computationally expensive. We recommend keeping this value odd in order to ensure there is an image at the midpoint.

=== "yaml"
    ``` yaml
    nimages: 5
    ```
=== "toml"
    ``` toml
    nimages = 5
    ```
=== "python"
    ``` python
    nimages = 5
    ```

!!! danger
    For calculators such as VASP, your `command` parameter must use a number of cores that is divisible by `nimages`. For example, `nimages=3` and `command="mpirun -n 10 vasp_std > vasp.out"` will fail because 10 is not divisible by 3.

--------------------------

## nsteadystate
The number of individual workflows to have scheduled at once. This therefore sets the queue size of an evolutionary search. Note, the number of workflows ran in parallel is determined by the number of `Workers` started (i.e. starting 3 workers will run 3 workflows in parallel, even if 100 workflows are in the queue). The steady-state does, however, set the **maximum** number of parallel runs because the queue size will never exceed the `nsteadystate` value. This parameter is closely tied with `steadystate_sources`, so be sure to read about that parameter as well.

=== "yaml"
    ``` yaml
    nsteadystate: 50
    ```
=== "toml"
    ``` toml
    nsteadystate = 50
    ```
=== "python"
    ``` python
    nsteadystate = 50
    ```

--------------------------

## nsteps
The total number of steps to run the calculation on. For example, in molecular dynamics workflows, this will stop the simulation after this many steps.

=== "yaml"
    ``` yaml
    nsteps: 10000
    ```
=== "toml"
    ``` toml
    nsteps = 10000
    ```
=== "python"
    ``` python
    nsteps = 10000
    ```

--------------------------

## percolation_mode
The percolating type to detect. The default is ">1d", which search for percolating
paths up to the `max_path_length`. Alternatively, this can be set to "1d" in order
to stop unique pathway finding when 1D percolation is achieved.

=== "yaml"
    ``` yaml
    percolation_mode: 1d
    ```
=== "toml"
    ``` toml
    percolation_mode = "1d"
    ```
=== "python"
    ``` python
    percolation_mode = "1d"
    ```

--------------------------

## run_id
The id assigned to a specific workflow run / calculation. If not provided this will be randomly generated, and we highly recommended leaving this at the default value. Note, this is based on unique-ids (UUID), so every id should be 100% unique and in a string format.

=== "yaml"
    ``` yaml
    run_id: my-unique-id-123
    ```
=== "toml"
    ``` toml
    run_id = "my-unique-id-123"
    ```
=== "python"
    ``` python
    run_id = "my-unique-id-123"
    ```

--------------------------

## search_id
(advanced users only)
The evolutionary search that this individual is associated with. This allows us to determine which `Selector`, `Validator`, and `StopCondition` should be used when creating and evaluating the individual. When running a search, this is set automatically when submitting a new flow.

--------------------------

## selector_kwargs
(advanced users only)
Extra conditions to use when initializing the selector class. `MySelector(**selector_kwargs)`. The input should be given as a dictionary. Note, for evolutionary searches, the composition kwarg is added automatically. This is closely tied with the `selector_name` parameter so be sure to read that section as well.

--------------------------

## selector_name
(experimental feature; advanced users only)
The base selector class that should be used. The class will be initialized using `MySelector(**selector_kwargs)`. The input should be given as a string.

!!! warning
    Currently, we only support truncated selection, so this should be left at its default value.

--------------------------

## singleshot_sources
(experimental feature; advanced users only)
A list of structure sources that run once and never again. This includes generating input structures from known structures (from third-party databases), prototypes, or substituiting known structures.

In the current version of simmate, these features are not enabled and this input should be ignored.

--------------------------

## sleep_step
When there is a cycle within a workflow (such as iteratively checking the number of subworkflows submitted and updating results), this is the amount of time in seconds that the workflow will shutdown before restarting the cycle. For evolutionary searches, setting this to a larger value will save on computation resources and database load, so we recommend increasing it where possible.

=== "yaml"
    ``` yaml
    run_id: 180
    ```
=== "toml"
    ``` toml
    run_id = 180
    ```
=== "python"
    ``` python
    sleep_step = 180  # 3 minutes
    ```

--------------------------

## source
(experimental feature; advanced users only)
This column indicates where the input data (and other parameters) came from. The source could be a number of things including...
 - a third party id
 - a structure from a different Simmate datbase table
 - a transformation of another structure
 - a creation method
 - a custom submission by the user

By default, this is a dictionary to account for the many different scenarios. Here are some examples of values used in this column:

=== "python"
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

--------------------------

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

=== "yaml"
    ``` yaml
    standardize_structure: primitive-LLL
    ```
=== "toml"
    ``` toml
    standardize_structure = "primitive-LLL"
    ```
=== "python"
    ``` python
    standardize_structure = "primitive-LLL"
    ```

--------------------------

## steadystate_source_id
(advanced users only)
The structure source that this individual is associated with. This allows us to determine how the new individual should be created. When running a search, this is set automatically when submitting a new flow.

--------------------------

## steadystate_sources
(experimental feature; advanced users only)
The sources that will be scheduled at a "steady-state", meaning there will always be a set number of individuals scheduled/running for this type of structure source. This should be defined as a dictionary where each is `{"source_name": percent}`. The percent determines the number of steady stage calculations that will be running for this at any given time. It will be a percent of the `nsteadystate` parameter, which sets the total number of individuals to be scheduled/running. For example, if `nsteadystate=40` and we add a source of `{"RandomSymStructure": 0.30, ...}`, this means 0.25*40=10 randomly-created individuals will be running/submitted at all times. The source can be from either the `toolkit.creator` or `toolkit.transformations` modules.

=== "yaml"
    ``` yaml
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
=== "yaml"
    ``` yaml
    [singleshot_sources]
    "RandomSymStructure": 0.30
    "from_ase.Heredity": 0.30
    "from_ase.SoftMutation": 0.10
    "from_ase.MirrorMutation": 0.10
    "from_ase.LatticeStrain": 0.05
    "from_ase.RotationalMutation": 0.05
    "from_ase.AtomicPermutation": 0.05
    "from_ase.CoordinatePerturbation": 0.05
    ```
=== "python"
    ``` python
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

Note: if your percent values do not sum to 1, they will be rescaled. When calculating `percent*nsteadystate`, the value will be rounded to the nearest integer.

We are moving towards accepting kwargs or class objects as well, but this is not yet allowed. For example, anything other than `percent` would be treated as a kwarg:

=== "toml"
    ``` toml
    [singleshot_sources.RandomSymStructure]
    percent: 0.30
    spacegroups_exclude: [1, 2, 3]
    site_generation_method: "MyCustomMethod"
    ```

--------------------------

## structure
The crystal structure to be used for the analysis. The input can be anything compatible with the `Structure` toolkit class. Accepted inputs include:

**a filename (cif or poscar) (recommended)**

=== "yaml"
    ``` yaml
    structure: NaCl.cif
    ```
=== "toml"
    ``` toml
    structure = NaCl.cif
    ```
=== "python"
    ``` python
    structure="NaCl.cif"
    ```

**a dictionary that points to a database entry.** 

=== "yaml"
    ``` yaml
    # example 1
    structure:
        database_table: MatprojStructure
        database_id: mp-123
        
    # example 2
    structure:
        database_table: StaticEnergy
        database_id: 50
    
    # example 3
    structure:
        database_table: Relaxation
        database_id: 50
        structure_field: structure_final
    ```
=== "toml"
    ``` toml
    # example 1
    [structure]
    database_table: MatprojStructure
    database_id: mp-123
        
    # example 2
    [structure]
    database_table: StaticEnergy
    database_id: 50
    
    # example 3
    [structure]
    database_table: Relaxation
    database_id: 50
    structure_field: structure_final
    ```
=== "python"
    ``` python
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

!!! note
    instead of `database_id`, you can also use the `run_id` or `directory` to indicate which entry to load. Further, if the database table is linked to multiple structures (e.g. relaxations have a `structure_start` and `structure_final`), then you can also add the `structure_field` to specify which to choose. 

**a `Structure` object (best for advanced logic)**

=== "python"
    ``` python
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

**a `Structure` database object**

=== "python"
    ``` python
    structure = ExampleTable.objects.get(id=123)
    ```

**json/dictionary serialization from pymatgen**

--------------------------

## subworkflow_kwargs
Make sure you read about `subworkflow_name` parameter first. This is a dictionary of parameters to pass to each subworkflow run. For example, the workflow will be ran as `subworkflow.run(**subworkflow_kwargs)`. Note, many workflows that use this argument will automatically pass information that is unique to each call (such as `structure`).

=== "yaml"
    ``` yaml
    subworkflow_kwargs:
        command: mpirun -n 4 vasp_std > vasp.out
        compress_output: true
    ```
=== "toml"
    ``` toml
    [subworkflow_kwargs]
    command = "mpirun -n 4 vasp_std > vasp.out"
    compress_output = true
    ```
=== "python"
    ``` python
    subworkflow_kwargs=dict(
        command="mpirun -n 4 vasp_std > vasp.out",
        compress_output=True,
    )
    ```

--------------------------

## subworkflow_name
The name of workflow that used to evaluate structures generated. For example, in evolutionary searches, individuals are created and then relaxed using the `relaxation.vasp.staged` workflow. Any workflow that is registered and accessible via the `get_workflow` utility can be used instead. (note: in the future we will allow unregisterd flows as well). If you wish to submit extra arguments to each workflow run, you can use the `subworkflow_kwargs` parameter.

=== "yaml"
    ``` yaml
    subworkflow_name: relaxation.vasp.staged
    ```
=== "toml"
    ``` toml
    subworkflow_name = "relaxation.vasp.staged"
    ```
=== "python"
    ``` python
    subworkflow_name = "relaxation.vasp.staged"
    ```

--------------------------

## supercell_end
The endpoint image supercell to use. This is really just a `structure` parameter under a different name, so everything about the `structure` parameter also applies here.

--------------------------

## supercell_start
The starting image supercell to use. This is really just a `structure` parameter under a different name, so everything about the `structure` parameter also applies here.

--------------------------

## symmetry_precision
If standardize_structure=True, then this is the cutoff value used to determine
if the sites are symmetrically equivalent. (in Angstroms)

=== "yaml"
    ``` yaml
    symmetry_precision: 0.1
    ```
=== "python"
    ``` python
    symmetry_precision = 0.1
    ```

--------------------------

## tags
When submitting workflows via the `run_cloud` command, tags are 'labels' that help control which workers are allowed to pick up and run the submitted workflow. Workers should be started with matching tags in order for these scheduled flows to run.

=== "yaml"
    ``` yaml
    tags:
        - my-tag-01
        - my-tag-02
    ```
=== "toml"
    ``` toml
    tags = ["my-tag-01", "my-tag-02"]
    ```
=== "python"
    ``` python
    tags = ["my-tag-01", "my-tag-02"]
    ```

!!! warning
    When you have a workflow that is submitting many smaller workflows (such as 
    `structure-prediction` workflows), make sure you set the tags in the
    `subworkflow_kwargs` settings:
    ``` yaml
    subworkflow_kwargs:
        tags:
            - my-tag-01
            - my-tag-02
    ```

--------------------------

## temperature_end
For molecular dynamics simulations, this is the temperature to end the simulation at (in Kelvin). This temperatue will be reached through a linear transition from the `temperature_start` parameter.

=== "yaml"
    ``` yaml
    temperature_end: 1000
    ```
=== "toml"
    ``` python
    temperature_end = 1000
    ```
=== "python"
    ``` python
    temperature_end = 1000
    ```

--------------------------

## temperature_start
For molecular dynamics simulations, this is the temperature to begin the simulation at (in Kelvin).

=== "yaml"
    ``` yaml
    temperature_start: 250
    ```
=== "toml"
    ``` toml
    temperature_start = 250
    ```
=== "python"
    ``` python
    temperature_start = 250
    ```

--------------------------

## time_step
For molecular dynamics simulations, this is time time between each ionic step (in femtoseconds).

=== "yaml"
    ``` yaml
    time_step: 1.5
    ```
=== "toml"
    ``` toml
    time_step = 1.5
    ```
=== "python"
    ``` python
    time_step = 1.5
    ```

--------------------------

## updated_settings
(experimental feature)
Unique to `customized.vasp.user-config`. This is a list of parameters to update the `workflow_base` with. This often involves updating the base class attributes.

--------------------------

## vacancy_mode
For NEB and diffusion workfows, this determines whether vacancy or interstitial
diffusion is analyzed. Default of True corresponds to vacancy-based diffusion.

=== "yaml"
    ``` yaml
    vacancy_mode: false
    ```
=== "toml"
    ``` toml
    vacancy_mode = false
    ```
=== "python"
    ``` python
    vacancy_mode = False
    ```

--------------------------

## validator_kwargs
(advanced users only)
Extra conditions to use when initializing the validator class. `MyValidator(**validator_kwargs)`. The input should be given as a dictionary. Note, for evolutionary searches, the composition kwarg is added automatically. This is closely tied with the `validator_name` parameter so be sure to read that section as well.

--------------------------

## validator_name
(experimental feature; advanced users only)
The base validator class that should be used. The class will be initialized using `MyValidator(**validator_kwargs)`. The input should be given as a string.

!!! warning
    Currently, we only support `CrystallNNFingerprint` validation, so this should be left at its default value.

--------------------------

## workflow_base
(experimental feature)
Unique to `customized.vasp.user-config`. This is the base workflow to use when updating critical settings.

--------------------------

## write_summary_files

Whether or not to write output files. For some workflows, writing output files can cause excessive load on the database and possibly make the calculation IO bound. In cases such as this, you can set this to `False`.

=== "yaml"
    ``` yaml
    write_summary_files: false
    ```
=== "toml"
    ``` toml
    write_summary_files = false
    ```
=== "python"
    ``` python
    write_summary_files = False
    ```
    
!!! tip
    Beginners can often ignore this setting. This is typically only relevant
    in a setup where you have many computational resources and have many
    evolutionary searches (>10) running at the same time.

--------------------------
