# Example Scripts

This section contains example Python scripts demonstrating the use of Simmate. These "recipes" provide a bridge between the basic tutorials and the full technical guides.

!!! warning
    These examples do *NOT* cover all the features of Simmate, but they are designed to show common real-world workflows.
    
    Before referring to these examples, make sure to check the "[Full Guides](../full_guides/overview.md)" and "[Apps](../apps/overview.md)" sections.

!!! note
    Have a cool script you'd like to share? We welcome community contributions! Check our [Contributing Guide](../full_guides/contributing/first_time_setup.md) to see how to add your own example here.

### Current Examples

| Goal | Level | Tags | Summary |
| :--- | :---: | :--- | :--- |
| [Data Mining & CIF Export](data_mining_and_cif_export.md) | **Beginner** | `DB` `MP` | Query stable structures from Materials Project and save locally. |
| [Symmetry-Breaking Strains](symmetry_breaking_strains.md) | **Beginner** | `Toolkit` | Apply lattice strains and detect resulting spacegroups. |
| [Structure Loading & I/O](structure_loading_and_io.md) | **Beginner** | `Toolkit` | Basic file interactions: loading CIF/POSCAR and calculating properties. |
| [Molecule Filtering](molecule_filtering.md) | **Beginner** | `Toolkit` `RDKit` | Load SDF files and filter molecules by chemical properties. |
| [Running Workflows via YAML](running_workflows_via_yaml.md) | **Beginner** | `Workflows` `CLI` | Configure and run a workflow using a simple YAML settings file. |
| [Chemical Composition Analysis](chemical_composition_analysis.md) | **Beginner** | `Toolkit` | Calculate formula weight, percentages, and oxidation state guesses. |
| [Single-Step VASP Relaxation](single_step_vasp_relaxation.md) | **Beginner** | `VASP` | A "Hello World" for simulations: run a relaxation from a CIF file. |
| [High-Throughput VASP Runs](high_throughput_vasp_runs.md) | **Intermediate** | `VASP` `MP` | Chain relaxation, static, and electronic structure for a list of materials. |
| [VASP + Bader Charge Analysis](vasp_plus_bader_charge_analysis.md) | **Intermediate** | `VASP` `Bader` | Run a relaxation and automatically calculate atomic charges. |
| [Machine Learning Featurization](machine_learning_featurization.md) | **Intermediate** | `ML` `DB` | Generate structural fingerprints for use in training ML models. |
| [Advanced NEB Path Finding](advanced_neb_path_finding.md) | **Advanced** | `VASP` `NEB` | Custom diffusion workflow with endpoint relaxations and image generation. |
| [Custom Evolutionary Search](custom_evolutionary_search.md) | **Advanced** | `CSP` `VASP` | Configure a search for new materials with specific structural constraints. |
