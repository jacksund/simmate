
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
