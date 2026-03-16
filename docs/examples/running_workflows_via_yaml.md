
# Running Workflows via YAML

## About :star:

This example demonstrates how to configure and run a Simmate workflow using a YAML settings file and the command-line interface. This is the recommended approach for most users as it keeps settings organized and easy to reproduce.

| Key Info        |                                            |
| --------------- | ------------------------------------------ |
| Contributor     | Simmate Team                               |
| Last updated    | 2026.03.14                                 |
| Level           | **Beginner**                               |

## Prerequisites :rotating_light:

- [x] Configure a database ([guide](/getting_started/workflows/configure_database.md))
- [x] Simulation software installed (e.g. VASP)

## The configuration :rocket:

First, create a sample structure file (like `NaCl.cif`):

``` bash
simmate toolkit make-structure NaCl
```

Next, create a file named `example.yaml` with your workflow settings:

``` yaml
# in example.yaml
workflow_name: relaxation.vasp.matproj
structure: NaCl.cif
command: mpirun -n 4 vasp_std > vasp.out
```

## The command :computer:

Run the workflow from your terminal:

``` shell
simmate workflows run example.yaml
```

Simmate will automatically:
1. Create a new directory for the task.
2. Load the structure and validate settings.
3. Execute the VASP command.
4. Parse results and save them to your local database.
5. Generate a `simmate_summary.yaml` file with the final results.
