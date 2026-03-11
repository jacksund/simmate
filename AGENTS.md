# Simmate Project Context

Simmate is a full-stack framework for chemistry and materials science research. It provides tools for workflow management, database interaction (using Django), and a toolkit for scientific computing.

## 🏗️ Project Layout

```text
simmate/
├── .github/                # CI/CD and contribution templates
├── docs/                   # MkDocs documentation
├── envs/                   # Docker and Helm configuration
├── src/
│   └── simmate/
│       ├── apps/           # Specialized modules (VASP, Materials Project, etc.)
│       ├── command_line/   # Typer CLI entry points
│       ├── configuration/  # Django and Simmate settings
│       ├── database/       # Django models and ORM infrastructure
│       ├── toolkit/        # Scientific objects (Structure, Molecule, etc.)
│       ├── utilities/      # General helper functions
│       ├── website/        # Django-based UI (HTMX, Unicorn)
│       ├── workflows/      # Core workflow engine and execution logic
│       ├── conftest.py     # Shared Pytest fixtures
│       └── __init__.py     # Package entry point
├── AGENTS.md               # This file
├── pyproject.toml          # Project metadata and dependencies
└── README.md
```

## 🛠️ Core Concepts

- **Apps (`simmate/apps/`):** Specialized modules for specific tools (e.g., VASP, Quantum Espresso), databases (e.g., Materials Project, AFLOW, ChEMBL, PubChem), or administrative tasks (e.g., Inventory Management, Project Management).
- **Toolkit (`simmate/toolkit/`):** Domain-specific objects like `Structure`, `Molecule`, `Composition`, `Spacegroup`, and utilities for symmetry, transformations, and featurization. These objects are primarily inherited from `pymatgen` or `rdkit`.
- **Database (`simmate/database/`):** Django-based models for storing and querying crystal structures, molecular data, and workflow results.
- **Workflows (`simmate/workflows/`):** Orchestrated sequences of computational tasks, often involving external software and database interactions.

## 🚀 Key Technologies

- **Language:** Python 3.11 (`>=3.11, <3.12`)
- **Web/DB Framework:** Django 5.2+ (with HTMX and Unicorn for dynamic UI)
- **CLI:** Typer (Primary entry point is `simmate`, with app-specific ones like `simmate-vasp`)
- **Scientific Libraries:** PyMatGen, ASE, RDKit, Pandas, NumPy, Matminer, Scikit-learn, LangChain (for AI agents)
- **Testing:** Pytest, Pytest-Django (Markers: `vasp`, `blender`, `pymatgen`, `slow`)
- **Documentation:** MkDocs with Material theme

## 🧩 App Structure (`src/simmate/apps/`)

Apps are specialized modules that follow a consistent (but optional) layout. Depending on an app's purpose (simulation, database access, UI), different components will be present.

- **`configuration.py`**: App-specific settings and logic (sometimes `config.py`).
- **`models/` or `models.py`**: Django models for database tables.
- **`migrations/`**: Database migration files (auto-generated).
- **`workflows/`**: App-specific workflows. Must be imported in `__init__.py`.
- **`inputs/` and `outputs/`**: File I/O utilities (e.g., VASP's INCAR/POSCAR).
- **`error_handlers/`**: Implementation of `ErrorHandler` classes (from `simmate.workflows`) to detect and fix runtime errors for scientific codes.
- **`command_line/` or `command_line.py`**: Custom CLI subcommands.
- **`urls.py`, `views.py`, `templates/`**: Web UI components (Django/HTMX).
- **`components/`**: HTMX-based UI components (using `simmate.website.htmx.components`).
- **`client.py` or `clients/`**: API clients for connecting to external services and databases (e.g., Materials Project, PubChem) to load data into Simmate.
- **`schedules.py` or `schedules/`**: Periodic tasks or automated update logic (used by `simmate engine start-schedules`).

**Note:** Most apps only use a subset of these. For example, data-only apps (like `materials_project`) lack I/O and error handlers, while simulation apps (like `vasp`) focus heavily on them.

## 🧪 Toolkit Details (`src/simmate/toolkit/`)

Pure scientific logic independent of the database.
- **`base_data_types/`**: Core objects (`Structure`, `Molecule`, `Composition`, `Reaction`) primarily wrapping Pymatgen/RDKit.
- **`symmetry/`**: Symmetry analysis, spacegroup detection, and standardization.
- **`transformations/`**: Structure/molecule manipulation (strain, supercells, substitutions).
- **`validators/`**: Physical/chemical validation logic for structures and results.
- **`visualization/`**: Rendering utilities for toolkit objects.
- **`featurizers/`**: Conversion of toolkit objects into machine-learning features.

## 🗄️ Database Architecture (`src/simmate/database/`)

Django-based infrastructure for scientific data management.
- **`base_data_types/`**: Abstract and concrete models for standard calculation types (`StaticEnergy`, `Relaxation`, `Dynamics`, `BandStructure`, `Thermodynamics`).
- **`workflow_results/`**: Re-exports base data types for easy access in app models.
- **`external_connectors/`**: Legacy scripts for external data syncing (use `client.py` in apps for new work).
- **Key Classes:**
    - `DatabaseTable`: Mixin with `from_toolkit()` for ORM-to-Scientific-Object conversion.
    - `Calculation`: Extends `DatabaseTable` with job metadata (`run_id`, `status`, `corrections`).
    - `Structure` (model): Mixin that adds `to_toolkit()` and stores core structure data.

## ⚙️ Workflows and Execution (`src/simmate/workflows/`)

Engine for running and monitoring computational tasks.
- **`base_flow_types/`**: 
    - `Workflow`: Base class for any automated task.
    - `S3Workflow`: Handles file-based codes (VASP/QE) with automated I/O and directory management.
    - `StagedWorkflow`: Manages multi-stage/chained runs with checkpointing.
- **`execution/`**: Backend for job submission and worker management (`executor.py`, `worker.py`).
- **`error_handler.py`**: Implementation of the `ErrorHandler` interface for fixing simulation failures.

## 📏 Coding Conventions

- **Type Hints:** Required for all new code.
- **Imports:** Use absolute imports (`from simmate.toolkit import Structure`).
- **File Paths:** Always use `pathlib.Path`.
- **Docstrings:** Use Google-style or standard Python docstrings.
- **Naming:** 
    - Database tables: PascalCase (e.g., `RelaxationRun`).
    - Workflows: `Type__App__Preset` (e.g., `Relaxation__Vasp__Matproj`).

## 🧪 Testing Best Practices

- **Fixtures:** Use fixtures from `src/simmate/conftest.py` (e.g. `structure`, `composition`).
- **Mocking:** Mock external scientific codes (VASP, QE) unless performing integration tests.
- **Cleanup:** Use `scratch_dir` pattern or Pytest's `tmp_path`.
- **Run Command:** `pytest -m "not vasp and not blender" --no-migrations`.

## 🤖 AI Agent Guidelines

- **Surgical Edits:** Favor `replace` for targeted changes in large files.
- **Validation:** Always run `pytest` and check for database migrations after model changes.
- **Migrations:** Run `simmate database update` for any model changes.
- **Dependencies:** Verify `pyproject.toml` before assuming a library is available.
- **Context:** Be aware of `scratch_dir` usage in workflows.
