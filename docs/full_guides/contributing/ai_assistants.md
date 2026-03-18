# Simmate Project Context

Simmate is a "batteries-included" full-stack framework for chemistry and materials science research. It bridges diverse simulation programs, third-party databases, and scientific utilities into a unified ecosystem. Core capabilities include:

- **Workflow Orchestration:** Scalable execution from local workstations to HPC clusters and Cloud (SLURM, Kubernetes).
- **Database Management:** A Django-based ORM for structured scientific data, integrating third-party datasets (Materials Project, COD, etc.).
- **Chemical Toolkit:** Simplified Pythonic interfaces for molecular (`rdkit`) and crystalline (`pymatgen`) analysis.
- **Web UI:** A dynamic HTMX/Django-based interface for managing workflows and exploring data.

This project is designed for both direct use in research and as a platform for building custom, data-driven chemistry applications.

## Project Layout

```text
simmate/
├── .github/                # CI/CD and contribution templates
├── docs/                   # MkDocs documentation
│   ├── full_guides/        # Deep-dive guides (CRITICAL for building new apps)
│   │   ├── apps/           # Creating and using custom apps
│   │   ├── compute_setup/  # HPC, Kubernetes, and local resources
│   │   ├── contributing/   # Developer setup and AI guidelines
│   │   ├── database/       # ORM, custom tables, and data management
│   │   ├── toolkit/        # Scientific objects (Structure, Molecule)
│   │   ├── website/        # UI, HTMX components, and REST API
│   │   └── workflows/      # Custom workflow creation
│   ├── apps/               # Quickstart guides for specific apps
│   ├── getting_started/    # Tutorial series for new users
│   └── change_log.md       # Change log for tracking updates
├── envs/                   # Docker and Helm configuration
├── src/
│   └── simmate/
│       ├── apps/           # Specialized modules (VASP, Materials Project, etc.)
│       ├── command_line/   # Typer CLI entry points
│       ├── config/         # Django/Simmate settings (Source of truth: load_settings.py)
│       ├── database/       # Django models and ORM infrastructure
│       ├── toolkit/        # Scientific objects (Structure, Molecule, etc.)
│       ├── utilities/      # General helper functions
│       ├── website/        # Django-based UI (and custom HTMX utils)
│       ├── workflows/      # Core workflow engine and execution logic
│       ├── conftest.py     # Shared Pytest fixtures
│       └── __init__.py     # Package entry point
├── pyproject.toml          # Project metadata and dependencies
└── README.md
```

## Core Concepts

- **Apps (`simmate/apps/`):** Specialized modules for specific tools (e.g., VASP), databases (e.g., Materials Project), or administrative tasks (e.g., Inventory Management).
- **Toolkit (`simmate/toolkit/`):** Domain-specific objects like `Structure`, `Molecule`, and `Composition`. These primarily wrap or inherit from `pymatgen` or `rdkit`.
- **Database (`simmate/database/`):** Django-based models and ORM infrastructure. Provides base models and mixins for application-specific data tables.
- **Workflows (`simmate/workflows/`):** Base classes and execution logic for building, monitoring, and distributing computational tasks.

## Key Technologies

- **Language:** Python
- **Web/DB:** Django (with HTMX for dynamic UI)
- **CLI:** Typer (Primary entry point: `simmate`)
- **Scientific:** PyMatGen, RDKit, Pandas, NumPy
- **Testing:** Pytest, Pytest-Django
- **Docs:** MkDocs (Material theme)

## App Structure (`src/simmate/apps/`)

Apps follow a consistent (though optional) layout depending on their purpose (simulation, database access, or UI).

- **`config.py`**: App-specific settings and logic.
- **`models.py` / `models/`**: Django models for database tables.
- **`migrations/`**: Auto-generated database migration files.
- **`workflows/`**: App-specific workflows (must be imported in `__init__.py`).
- **`inputs/` & `outputs/`**: File I/O utilities for external codes.
- **`error_handlers/`**: `ErrorHandler` implementations to detect and fix runtime errors.
- **`command_line/`**: Custom CLI subcommands.
- **`urls.py`, `views.py`, `templates/`**: Web UI components (Django/HTMX).
- **`components/`**: HTMX-based UI components (via `simmate.website.htmx.components`).
- **`client.py`**: API clients for external services (e.g., Materials Project, PubChem).
- **`schedules/`**: Periodic tasks (used by `simmate engine start-schedules`).

## Toolkit Details (`src/simmate/toolkit/`)

Scientific logic independent of the database.

- **`base_data_types/`**: Core objects (`Structure`, `Molecule`, `Composition`) wrapping Pymatgen/RDKit.
- **`symmetry/`**: Analysis, spacegroup detection, and standardization.
- **`transformations/`**: Manipulation (strain, supercells, substitutions).
- **`validators/`**: Physical and chemical validation logic.
- **`visualization/`**: Rendering utilities for toolkit objects.
- **`featurizers/`**: ML feature generation from toolkit objects.

## Database Architecture (`src/simmate/database/`)

- **`base_data_types/`**: Abstract and concrete models for standard calculation types (e.g., `StaticEnergy`, `Relaxation`, `Dynamics`).
- **`workflow_results/`**: Re-exports base types for app models.
- **`external_connectors/`**: Legacy syncing scripts (use `client.py` in apps for new work).
- **Key Classes:**
    - `DatabaseTable`: Mixin with `from_toolkit()` for ORM-to-Scientific conversion.
    - `Calculation`: Extends `DatabaseTable` with job metadata (`run_id`, `status`).
    - `Structure` (model): Mixin that adds `to_toolkit()` and stores core structure data.

## Workflows and Execution (`src/simmate/workflows/`)

- **`base_flow_types/`**: 
    - `Workflow`: Base class for any automated task.
    - `S3Workflow`: Handles file-based codes (VASP/QE) with automated I/O.
    - `StagedWorkflow`: Manages multi-stage/chained runs.
- **`execution/`**: Backend for job submission and worker management.
- **`error_handler.py`**: Interface for fixing simulation failures.

## Coding Conventions

- **Type Hints:** Required for all new code. Keep them simple and use built-in types.
- **File Paths:** Always use `pathlib.Path`.
- **Docstrings:** Use Google-style docstrings.
- **Formatting:** Adhere to `black` and `isort` conventions.

## Testing & Validation

- **Fixtures:** Use `src/simmate/conftest.py` (e.g., `structure`, `composition`).
- **Mocking:** Mock external scientific codes unless performing integration tests.
- **Commands:**
    - Test: `pytest .`
    - Lint: `black .`, `isort .`, `djlint .`
    - Migrations: `simmate database update` (generates and applies migrations).

## AI Agent Guidelines

- **Surgical Edits:** Favor `replace` for targeted changes in large files.
- **Dependencies:** Verify `pyproject.toml` before assuming a library is available.
- **Documentation:** Always refer to `docs/full_guides/` when building new apps or workflows. These guides provide essential architectural patterns, naming conventions, and best practices.
- **Change Log:** Always document your changes in the changelog.
