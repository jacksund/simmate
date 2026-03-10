# Simmate Workflows and Execution

Workflows are the primary way to perform computational tasks in Simmate. They are orchestrated sequences of steps that often involve calling external software and logging results to the database.

## Workflow Types

- **`Workflow` (Generic):** The most flexible base class. It provides the standard `.run()` interface and can be used for any orchestrated set of tasks.
- **`S3Workflow`:** A common base class (located in `simmate.workflows.base_flow_types`). It handles input validation, directory management, and error handling for external command executions (specifically those that produce input/output files).
- **`StagedWorkflow`:** Designed for workflows that are broken into distinct stages (e.g., a series of VASP relaxations). It provides logic for managing the transition between stages and handling intermediate results.
- **`StructureWorkflow`:** Specialized for workflows where the primary input is a `Structure`.

## Key Features

- **Execution Engine:** Workflows can be run locally, through a scheduler, or distributed across clusters.
- **Error Handling:** `simmate.workflows.error_handler` provides sophisticated logic for detecting and correcting common failures in scientific codes (e.g., VASP convergence issues).
- **Caching:** Many workflows automatically cache results in the database to avoid redundant calculations.
- **Parameters:** Workflows use a standard set of parameters defined in `docs/parameters/` (e.g., `structure`, `command`, `directory`).

## Common Patterns

- **Naming Convention:** Workflows follow a `Type__App__Preset` format (e.g., `Relaxation__Vasp__Matproj`). This class name is used to automatically determine `name_type`, `name_app`, and `name_preset`.
- **Database Table Mapping:** The `database_table` property on a workflow is often automatically determined based on its `name_type` (e.g., "relaxation" workflows use the `Relaxation` table).
- **Initialization:** `MyWorkflow.run(structure=..., directory=...)`.
- **Results:** Results are stored in the mapped database table, which should use the `Calculation` mixin.

## Command Line Integration

Workflows are often exposed via the CLI:
`simmate-vasp workflow run vasp/relaxation -s Fe1 -d test_dir`
