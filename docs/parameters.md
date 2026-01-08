# Parameters

## Introduction

### About

This section provides a detailed overview of all unique parameters for all workflows.

To identify the parameters allowed for a specific workflow, use the `explore` command or `workflow.show_parameters()`:

=== "command line"
    ``` bash
    simmate workflows explore
    ```

=== "python"

    ``` python
    workflow.show_parameters()
    ```

### File vs. Python formats

When switching from Python to YAML, make sure you adjust the input format of your parameters. This is especially important if you use python a `list` or `dict` for one of your input parameters. Further, if you have complex input parameters (e.g. nested lists, matricies, etc.), we recommend using a TOML input file instead:

=== "lists"
    ``` python
    # in python
    my_parameter = [1,2,3]
    ```
    ``` yaml
    # in yaml
    my_parameter:
        - 1
        - 2
        - 3
    ```

=== "dictionaries"
    ``` python
    # in python
    my_parameter = {"a": 123, "b": 456, "c": ["apple", "orange", "grape"]}
    ```
    ``` yaml
    # in yaml
    my_parameter:
        a: 123
        b: 456
        c:
            - apple
            - orange
            - grape
    ```
    ``` toml
    # in toml
    [my_parameter]
    a = 123
    b = 456
    c = ["apple", "orange", "grape"]
    ```

=== "nested lists"
    ``` python
    # in python
    my_parameter = [
        [1, 2, 3],
        [4, 5, 6],
        [7, 8, 9],
    ]
    ```
    ``` yaml
    # in yaml (we recommend switching to TOML!)
    my_parameter:
        - - 1
            - 2
            - 3
        - - 4
            - 5
            - 6
        - - 7
            - 8
            - 9
    ```
    ``` toml
    # in toml
    my_parameter = [
        [1, 2, 3],
        [4, 5, 6],
        [7, 8, 9],
    ]
    ```

=== "tuple"
    ``` python
    # in python
    my_parameter = (1,2,3)
    ```
    ``` yaml
    # in yaml
    my_parameter:
        - 1
        - 2
        - 3
    # WARNING: This will return a list! Make sure you call 
    #   `tuple(my_parameter)`
    # at the start of your workflow's `run_config` if you need a tuple.
    ```
    ``` toml
    # in toml
    my_parameter = [1, 2, 3]
    # WARNING: This will return a list! Make sure you call 
    #   `tuple(my_parameter)`
    # at the start of your workflow's `run_config` if you need a tuple.
    ```


--------------------------


## angle_tolerance
This parameter is used to determine if the angles between sites are symmetrically equivalent when `standardize_structure=True`. The value is in degrees.

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

## chemical_system
This parameter specifies the chemical system to be used in the analysis. It should be given as a string in the format `Element1-Element2-Element3-...`. For example, `Na-Cl`, `Y-C`, and `Y-C-F` are valid chemical systems.

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
This parameter specifies the command that will be called during the execution of a program. There is typically a default set for this that you only need to change if you'd like parallelization. For example, VASP workflows use `vasp_std > vasp.out` by default but you can override this to use `mpirun`.

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

--------------------------

## compress_output
This parameter determines whether to compress the `directory` to a zip file at the end of the run. After compression, it will also delete the directory. The default is False.

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

## copy_previous_directory
This parameter determines whether to copy the directory from the previous calculation (if one exists) and use it as a starting point for the new calculation. This is only possible if you provided an input that points to a previous calculation. For instance, `structure` would need to use a database-like input:

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

## diffusion_analysis_id
(advanced users only) This is the entry id from the `DiffusionAnalysis` table to link the results to. This is set automatically by higher-level workflows and rarely (if ever) set by the user.

--------------------------

## directory
This is the directory where everything will be run -- either as a relative or full path. This is passed to the utilities function `simmate.ulitities.get_directory`, which generates a unique folder name if not provided (such as `simmate-task-12390u243`). This will be converted into a `pathlib.Path` object. Accepted inputs include:

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
Exclusive to the `restart.simmate.automatic` workflow, this is the folder where the workflow will be continued. It follows the same rules/inputs as the `directory` parameter.

--------------------------

## directory_old
Exclusive to the `restart.simmate.automatic` workflow, this is the original folder that should be used as the starting point. It follows the same rules/inputs as the `directory` parameter.


--------------------------

## fitness_field
(advanced users only)
For evolutionary searches, this is the value that should be optimized. Specifically, it should minimize this value (lower value = better fitness). The default is `energy_per_atom`, but you may want to set this to a custom column in a custom database table.

--------------------------

## input_parameters
(experimental feature)
Exclusive to `customized.vasp.user-config`. This is a list of parameters to pass to `workflow_base`.

--------------------------

## is_restart
(experimental feature)
This parameter indicates whether the calculation is a restarted workflow run. The default is False. If set to true, the workflow will go through the given directory (which must be provided) and determine where to resume.

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
For diffusion workflows, this is the maximum length allowed for a single path.

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
This is the maximum stoichiometric ratio that will be analyzed. In a binary system evolutionary search, this will only look at non-reduced compositions up to the max_stoich_factor. For example, this means Ca2N and max factor of 4 would only look up to Ca8N4 and skip any compositions with more atoms (e.g. Ca10N5 is skipped)

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
    For apps such as VASP, your `command` parameter must use a number of cores that is divisible by `nimages`. For example, `nimages=3` and `command="mpirun -n 10 vasp_std > vasp.out"` will fail because 10 is not divisible by 3.

--------------------------

## nsteadystate
This parameter sets the number of individual workflows to be scheduled at once, effectively setting the queue size of an evolutionary search. The number of workflows run in parallel is determined by the number of `Workers` started. However, the `nsteadystate` value sets the **maximum** number of parallel runs as the queue size will never exceed this value. This parameter is closely tied with `steadystate_sources`.

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
This parameter sets the total number of steps for the calculation. For instance, in molecular dynamics workflows, the simulation will stop after this many steps.

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
This parameter sets the percolating type to detect. The default is ">1d", which searches for percolating paths up to the `max_path_length`. Alternatively, this can be set to "1d" to stop unique pathway finding when 1D percolation is achieved.

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

## relax_bulk
This parameter determines whether the bulk structure (typically the input structure) should be relaxed before running the rest of the workflow.

=== "yaml"
    ``` yaml
    relax_bulk: false
    ```
=== "toml"
    ``` toml
    relax_bulk: false
    ```
=== "python"
    ``` python
    relax_bulk: false
    ```

--------------------------

## relax_endpoints
This parameter determines whether the endpoint structures for an NEB diffusion pathway should be relaxed before running the rest of the workflow.

=== "yaml"
    ``` yaml
    relax_endpoints: false
    ```
=== "toml"
    ``` toml
    relax_endpoints: false
    ```
=== "python"
    ``` python
    relax_endpoints: false
    ```

--------------------------

## run_id
This parameter is the id assigned to a specific workflow run/calculation. If not provided, this will be randomly generated. It is highly recommended to leave this at the default value. This id is based on unique-ids (UUID), so every id should be 100% unique and in a string format.

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
This parameter is the evolutionary search that this individual is associated with. This allows us to determine which `Selector`, `Validator`, and `StopCondition` should be used when creating and evaluating the individual. When running a search, this is set automatically when submitting a new flow.

--------------------------

## selector_kwargs
(advanced users only)
This parameter is a dictionary of extra conditions to use when initializing the selector class. `MySelector(**selector_kwargs)`. This is closely tied with the `selector_name` parameter.

--------------------------

## selector_name
(experimental feature; advanced users only)
This parameter is the base selector class that should be used. The class will be initialized using `MySelector(**selector_kwargs)`. The input should be given as a string.

!!! warning
    Currently, we only support truncated selection, so this should be left at its default value.

--------------------------

## singleshot_sources
(experimental feature; advanced users only)
This parameter is a list of structure sources that run once and never again. This includes generating input structures from known structures (from third-party databases), prototypes, or substituting known structures.

In the current version of simmate, these features are not enabled and this input should be ignored.

--------------------------

## sleep_step
This parameter is the amount of time in seconds that the workflow will shutdown before restarting the cycle when there is a cycle within a workflow (such as iteratively checking the number of subworkflows submitted and updating results). For evolutionary searches, setting this to a larger value will save on computation resources and database load, so we recommend increasing it where possible.

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
This parameter indicates where the input data (and other parameters) came from. The source could be a number of things including a third party id, a structure from a different Simmate database table, a transformation of another structure, a creation method, or a custom submission by the user.

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
This parameter determines whether to standardize the structure during our setup(). This means running symmetry analysis on the structure to reduce the symmetry and convert it to some standardized form. There are three different forms to choose from and thus 3 different values that `standardize_structure` can be set to:

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
This parameter is the structure source that this individual is associated with. This allows us to determine how the new individual should be created. When running a search, this is set automatically when submitting a new flow.

--------------------------

## steadystate_sources
(experimental feature; advanced users only)
This parameter is a dictionary of sources that will be scheduled at a "steady-state", meaning there will always be a set number of individuals scheduled/running for this type of structure source. This should be defined as a dictionary where each is `{"source_name": percent}`. The percent determines the number of steady stage calculations that will be running for this at any given time. It will be a percent of the `nsteadystate` parameter, which sets the total number of individuals to be scheduled/running. For example, if `nsteadystate=40` and we add a source of `{"RandomSymStructure": 0.30, ...}`, this means 0.25*40=10 randomly-created individuals will be running/submitted at all times. The source can be from either the `toolkit.creator` or `toolkit.transformations` modules.

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
=== "toml"
    ``` toml
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

## stop_conditions
(experimental feature; advanced users only)
This parameter provides a set of stop conditions that will be checked periodically to determine if a FixedComposition evolutionary search should be stopped. It should be defined as a dictionary where each key is the string name of a StopCondition and the value is any kwargs that are needed to instantiate the class.

=== "yaml"
    ``` yaml
    stop_conditions:
        BasicStopConditions:
            max_structures: 1000
            min_structures_exact: 100
            convergence_cutoff: 0.001
            best_survival_cutoff: 100
        ExpectedStructure:
            structure: NaCl.cif
    ```
=== "toml"
    ``` toml
    [stop_conditions.BasicStopConditions]
    max_structures = 1000
    min_structures_exact = 100
    convergence_cutoff = 0.001
    best_survival_cutoff = 100
    [stop_conditions.ExpectedStructure]
    structure: NaCl.cif
    ```
=== "python"
    ``` python
    stop_conditions = {
        "BasicStopConditions": {
        "max_structures": 1000,
        "min_structures_exact": 100,
        "convergence_cutoff": 0.001
        "best_survival_cutoff": 100
        },
        "ExpectedStructure": {
        "structure": "NaCl.cif"
        },
    }
    ```
Currently, only the BasicStopConditions and ExpectedStructure stop conditions are supported. They each have the following subparameters

**BasicStopConditions**
The `BasicStopConditions` are those that are important to all searches. If this `StopCondition` is not provided, defaults will be constructed.

### max_structures
The maximum number of structures generated. The search will end at this number of structures regardless of if the search has converged. If not provided, the workflow estimates a reasonable value based on the number of atoms.

!!! warning
    `min_structure_exact` takes priority over this setting, so it is possible 
    for your search to exceed your maximum number of structures. If you want 
    `max_structures` to have absolute control, you can set `min_structure_exact` 
    to 0.

### min_structures_exact
The minimum number of structures that must be calculated with exactly matching nsites as specified in fixed-composition. If not provided, the workflow estimates a reasonable value based on the number of atoms.

### convergence_cutoff
The search will be considered converged when the best structure is not changing by this amount (in eV). In order to officially signal the end of the search, the best structure must survive within this convergence limit for a specific number of new individuals -- this is controlled by the best_survival_cutoff. The default of 1meV is typically sufficient and does not need to be changed. More often, users should update best_survival_cutoff instead.

### best_survival_cutoff
The search will stop when the best individual remains unbeaten for this number of new individuals.

To account for similar structures (e.g., identical structures with minor energy differences), structures within the convergence_cutoff parameter (e.g., +1meV) are not considered when counting historical structures. This helps to prevent the search from continuing in cases where the search is likely already converged but making <0.1meV improvements. If not provided, the workflow estimates a reasonable value based on the number of atoms.

**ExpectedStructure**
The `ExpectedStructure` stop condition will compare all structures generated in the search to a provided structure and immediately halt the search if there is a match.

### expected_structure
When a structure is found in the search that matches this structure, the search will be stopped. The allowed inputs follow the same scheme as in the Structure parameter.

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
This parameter is a dictionary of parameters to pass to each subworkflow run. For example, the workflow will be ran as `subworkflow.run(**subworkflow_kwargs)`. Note, many workflows that use this argument will automatically pass information that is unique to each call (such as `structure`).

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
This parameter is the name of workflow that used to evaluate structures generated. Any workflow that is registered and accessible via the `get_workflow` utility can be used instead. If you wish to submit extra arguments to each workflow run, you can use the `subworkflow_kwargs` parameter.

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
This parameter is the endpoint image supercell to use. This is really just a `structure` parameter under a different name, so everything about the `structure` parameter also applies here.

--------------------------

## supercell_start
This parameter is the starting image supercell to use. This is really just a `structure` parameter under a different name, so everything about the `structure` parameter also applies here.

--------------------------

## symmetry_precision
If standardize_structure=True, then this is the cutoff value used to determine if the sites are symmetrically equivalent. (in Angstroms)

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

When no tags are set, the following default tags will be used for a Simmate workflow:

- [x] `simmate` (this is the default worker tag as well)
- [x] the workflow's type name
- [x] the workflow's app name
- [x] the full workflow name

For example, the `static-energy.vasp.matproj` would have the following tags:
``` yaml
- simmate
- static-energy
- vasp
- static-energy.vasp.matproj
```

To override these default tags, use the following:

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

!!! bug
    Filtering tags does not always work as expected in SQLite3 because a worker with 
    `my-tag` will incorrectly grab jobs like `my-tag-01` and `my-tag-02`. This
    issue is known by both [Django](https://docs.djangoproject.com/en/4.2/ref/databases/#substring-matching-and-case-sensitivity) and [SQLite3](https://www.sqlite.org/faq.html#q18). Simmate addresses this issue by requiring all
    tags to be 7 characters long AND fully lowercase when using SQLite3.

--------------------------

## temperature_end
For molecular dynamics simulations, this is the temperature to end the simulation at (in Kelvin). This temperature will be reached through a linear transition from the `temperature_start` parameter.

=== "yaml"
    ``` yaml
    temperature_end: 1000
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
For NEB and diffusion workfows, this determines whether vacancy or interstitial diffusion is analyzed. Default of True corresponds to vacancy-based diffusion.

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
This parameter is a dictionary of extra conditions to use when initializing the validator class. `MyValidator(**validator_kwargs)`. This is closely tied with the `validator_name` parameter.

--------------------------

## validator_name
(experimental feature; advanced users only)
This parameter is the base validator class that should be used. The class will be initialized using `MyValidator(**validator_kwargs)`. The input should be given as a string.

!!! warning
    Currently, we only support `CrystallNNFingerprint` validation, so this should be left at its default value.

--------------------------

## workflow_base
(experimental feature)
Unique to `customized.vasp.user-config`. This is the base workflow to use when updating critical settings.

--------------------------

## write_summary_files

This parameter determines whether or not to write output files. For some workflows, writing output files can cause excessive load on the database and possibly make the calculation IO bound. In cases such as this, you can set this to `False`.

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