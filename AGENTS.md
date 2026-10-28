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
├── docs/                   # Zensical documentation (config in zensical.toml)
│   ├── full_guides/        # Deep-dive guides (CRITICAL for building new apps)
│   │   ├── apps/           # Creating and using custom apps
│   │   ├── compute/        # Workers, HPC (SLURM), Kubernetes, and schedules
│   │   ├── contributing/   # Developer setup and maintainer notes
│   │   ├── database/       # ORM, custom tables, and data management
│   │   ├── toolkit/        # Scientific objects (Structure, Molecule)
│   │   ├── website/        # UI, HTMX components, and REST API
│   │   └── workflows/      # Custom workflow creation
│   ├── apps/               # Quickstart guides for specific apps
│   ├── examples/           # Worked examples and recipes
│   ├── getting_started/    # Tutorial series for new users
│   └── change_log/         # Change log for tracking updates
├── envs/                   # Docker, Helm, and nginx/postgres configs
├── src/
│   └── simmate/
│       ├── apps/           # Specialized modules (VASP, Materials Project, etc.)
│       ├── command_line/   # Typer CLI entry points
│       ├── compute/        # Backend for job submission and worker management
│       ├── config/         # Django/Simmate settings (Source of truth: load_settings.py)
│       ├── database/       # Django models and ORM infrastructure
│       ├── desktop/        # Qt (PySide6) desktop app (`simmate desktop start`)
│       ├── toolkit/        # Scientific objects (Structure, Molecule, etc.)
│       ├── utils/          # General helper functions
│       ├── website/        # Django-based UI (and custom HTMX utils)
│       ├── workflows/      # Core workflow engine and execution logic
│       ├── conftest.py     # Shared Pytest fixtures
│       └── __init__.py     # Package entry point
├── pyproject.toml          # Project metadata and dependencies
├── zensical.toml           # Docs site config (nav, theme, markdown extensions)
└── README.md
```

## Core Concepts

- **Apps (`simmate/apps/`):** Specialized modules for specific tools (e.g., VASP), databases (e.g., Materials Project), or administrative tasks (e.g., Inventory Management).
- **Toolkit (`simmate/toolkit/`):** Domain-specific objects like `Structure`, `Molecule`, and `Composition`. These primarily wrap or inherit from `pymatgen` or `rdkit`.
- **Database (`simmate/database/`):** Django-based models and ORM infrastructure. Provides base models and mixins for application-specific data tables.
- **Workflows (`simmate/workflows/`):** Base classes and execution logic for building, monitoring, and distributing computational tasks.

## Key Technologies

- **Language:** Python 3.13
- **Web/DB:** Django (with HTMX for dynamic UI)
- **CLI:** Typer (Primary entry point: `simmate`)
- **Scientific:** PyMatGen, RDKit, Pandas, Polars (datastores and archives), NumPy
- **Desktop:** PySide6 (optional `desktop` extra)
- **Testing:** Pytest, Pytest-Django
- **Docs:** Zensical (successor to MkDocs Material; `simmate dev docs` serves locally)

## App Structure (`src/simmate/apps/`)

Apps follow a consistent (though optional) layout depending on their purpose (simulation, database access, or UI).

- **`config.py`**: `test_config()` checks used by `simmate config test`. (Each app's Django `AppConfig` lives centrally in `simmate/apps/configs.py`.)
- **`models.py` / `models/`**: Django models for database tables.
- **`migrations/`**: Auto-generated database migration files.
- **`workflows/`**: App-specific workflows. Classes must be imported in `workflows/__init__.py` (or listed in its `__all__`) to be discovered.
- **`inputs/` & `outputs/`**: File I/O utilities for external codes.
- **`error_handlers/`**: `ErrorHandler` implementations to detect and fix runtime errors.
- **`command_line/`**: Custom CLI subcommands.
- **`urls.py`, `views.py`, `templates/`**: Web UI components (Django/HTMX).
- **`components/`**: HTMX-based UI components (via `simmate.website.htmx.components`).
- **`client.py`**: API clients for external services (e.g., Materials Project, PubChem).
- **`datastores/`**: `Datastore` subclasses for very large datasets (see Datastores below).
- **`schedules.py`**: Periodic tasks (used by `simmate compute scheduler start`).

## Toolkit Details (`src/simmate/toolkit/`)

Scientific logic independent of the database. Look here first for reusable tools before writing new chemistry or analysis code. The key packages are below, but there are many more worth checking.

- **`base_data_types/`**: Core objects (`Structure`, `Molecule`, `Composition`, `Reaction`) wrapping Pymatgen/RDKit.
- **`datastores/`**: Parquet-backed storage and search for very large datasets (see Datastores below).
- **`featurizers/`**: Fingerprints and ML features (ECFP4, MACCS, Morgan, etc.).
- **`filters/`, `similarity/`, `clustering/`, `mapping/`**: Molecule screening and analysis (SMARTS and duplicate filters, Tanimoto and other similarity metrics, Butina/k-means clustering, PCA/t-SNE/UMAP).
- **`modeling/`**: Models that predict a column from inputs like properties or fingerprint bits (`Predictor` subclasses with `cross_validate`: Ridge, random forest, gradient boosting, Tanimoto k-NN), plus `LinearFit` for least-squares fits with p-values.
- **`symmetry/`, `transformations/`, `creators/`, `validators/`**: Crystal tools (Wyckoff/spacegroup data, strains and perturbations, random structure generation, structure validation).
- **`file_converters/`**: Readers and writers for molecule and structure file formats.
- **`visualization/`**: Plotting and rendering utilities for toolkit objects.

## Datastores (`src/simmate/toolkit/datastores/`)

For datasets too large for ORM queries (millions of rows, e.g. ChEMBL or Chemspace molecules).

- **`Datastore`**: Base class. Stores parquet chunks under `~/simmate/<app_name>/datastores/<datastore_name>/` in `staging/`, `live/`, and `old/` folders (`promote_staging()` swaps staging into live). Query with polars via `lf`, `filter()`, and `get_row()`.
- **`MoleculeDatastore`**: Adds molecule property and fingerprint columns, plus similarity search through `vector_indexes/` (usearch HNSW, faiss IVF-PQ).
- **App datastores**: Subclass in an app's `datastores/` folder and set `app_name` and `datastore_name` (e.g. `apps/chembl/datastores/molecules.py`).

## Database Architecture (`src/simmate/database/`)

- **`core/`**: Fundamental base models for all database tables (e.g., `DatabaseTable`, `SearchResults`).
- **`mixins/`**: Standardized reusable model mixins for scientific data (e.g., `Structure`, `Relaxation`, `Calculation`).
- **`workflow_results/`**: Re-exports base types for app models.
- **`external_connectors/`**: Base connectors for external services (`S3Bucket`, `WebScraper`, SSH, Oracle/MS SQL/Trino). Used by app `client.py` files and maintenance workflows.
- **Key Classes:**
    - `DatabaseTable`: Base model with `from_toolkit()` support, plus `ArchiveMixin` for loading and exporting data archives. (`to_toolkit()` lives on `SearchResults` and on mixins like `Structure`.)
    - `Calculation`: Extends `DatabaseTable` with job metadata (`run_id`, `status`).
    - `Structure` (mixin): Adds `to_toolkit()` and stores core structure data (lattice, sites).
- **Model Conventions:** Declare fields with `table_column` (`from simmate.database.core import DatabaseTable, table_column`), e.g. `table_column.CharField(...)` instead of `models.CharField`. Put a docstring directly under each field; `get_column_docs()` and `show_table_docs()` read these as column descriptions.

## Website Architecture (`src/simmate/website/`)

The web interface is built with Django and HTMX.

- **`server/`**: The root Django project's URLs, views, and ASGI/WSGI entry points. (Django settings live in `config/django/settings.py`.)
- **`core/`**: Shared components, templates, static files, and base models for the UI.
- **`data_explorer/`**: App for searching and exploring database tables.
- **`workflow_explorer/`**: App for submitting workflows and viewing results/analytics.
- **`compute_management/`**: Compute dashboard, WorkItem/Worker tables, and routes for the worker REST API (served at `/apps/compute/`; views live in `compute/api/`).
- **`htmx/`**: Base classes and utilities for HTMX-based components.

## Workflows and Execution (`src/simmate/workflows/` & `src/simmate/compute/`)

- **`src/simmate/workflows/core/`**:
    - `Workflow`: Base class for any automated task.
    - `ErrorHandler`: Interface for fixing simulation failures.
- **`src/simmate/workflows/common/`**:
    - `S3Workflow`: Handles file-based codes (VASP/QE) with automated I/O.
    - `StagedWorkflow`: Manages multi-stage/chained runs.
- **`src/simmate/compute/`**: Backend for job submission and worker management (Executor, Worker, and Scheduler). Its models are registered under `website/compute_management/`.
- **Naming:** Workflow classes are named `Type__App__Preset` (e.g. `StaticEnergy__Vasp__MatProj` is `static-energy.vasp.matproj`). See `docs/full_guides/workflows/naming_conventions.md`.

## Coding Conventions

- **Type Hints:** Required for all new code. Keep them simple and use built-in types.
- **File Paths:** Always use `pathlib.Path`.
- **Logging:** Use the shared simmate logger (`from simmate.utils import logger`) instead of the root logger (`logging.info(...)`).
- **Docstrings:** Use Google-style docstrings (`Args:`, `Returns:`). Some older code uses a markdown `#### Parameters` style; don't copy it.
- **Formatting:** Use `ruff` for Python (linting, formatting, and import sorting) and `djlint` for HTML templates (`simmate dev lint` runs both). Lint rules are ruff's defaults minus the `ignore` list in `pyproject.toml`. Don't add `# -*- coding: utf-8 -*-` headers.
- **Import Order:** `from simmate.database import connect` sets up Django, so it must come before model imports. Pin it with `# ruff: isort: skip` (or `# ruff: isort: skip_file` for whole files with circular-import ordering).
- **Toolkit First:** Put rdkit/pymatgen logic on toolkit objects (e.g. add a `Molecule.get_example_property()` method). Do not import `rdkit` or `pymatgen` directly in apps, datastores, or models; extend the toolkit instead. Existing direct pymatgen imports (e.g. in `apps/vasp/` and some database mixins) are legacy; don't copy them.
- **No One-Off Helpers:** Only pull logic out into a helper when it is reused in several places. Otherwise write it inline (with a short comment if needed) so the method reads top to bottom.
- **Scripts:** Don't add `if __name__ == "__main__":` guards (scripts are run directly in Spyder). Keep one-off scripts minimal.

## Testing & Validation

- **Fixtures:** Use `src/simmate/conftest.py` (e.g., `structure`, `composition`).
- **Mocking:** Mock external scientific codes unless performing integration tests.
- **When Not to Add Tests:** Don't add unit tests for infra/deployment changes (workers, k8s, signal handling) or for features whose design is still in flux; give manual test steps instead. Running existing tests to check nothing broke is fine.
- **Commands:**
    - Test: `simmate dev test`
    - Lint: `simmate dev lint` (ruff, djlint)
    - Migrations: `simmate database update` (generates and applies migrations).

## AI Agent Guidelines

- **Dependencies:** Verify `pyproject.toml` before assuming a library is available.
- **Documentation:** Always refer to `docs/full_guides/` when building new apps or workflows. These guides provide essential architectural patterns, naming conventions, and best practices.
- **Change Log:** Do not update `docs/change_log/` during sessions. The maintainer writes change log entries themselves.
- **Keep It Simple:** Start with the simplest design that is correct for the current use case. Suggest scale or performance improvements (indexes, caching, locking) as follow-ups instead of building them up front.
- **Database Changes:** Always ask the user before running anything that modifies the database (migrations, resets, data loads, deletes).
- **Git Worktrees:** Sessions started in a git worktree share the local dev database with the main repo, so they must NEVER apply migrations or otherwise modify the database. Any work that involves the database is done from the main repo instead. If a worktree needs its own Python environment, set it up with `uv sync --all-extras`.
- **Discuss Before Planning:** For open-ended design questions (e.g. "look into X"), lay out the options and tradeoffs and give a recommendation. Wait for a direction before writing an implementation plan.
- **Git:** Leave all changes unstaged. Never stage, commit, or push unless the user explicitly asks. When asked to commit or push, use a one-line commit message only (no description body), and do not add AI co-author signatures or any mention of AI/Claude.
- **Keep This File Current:** If your changes make anything in AGENTS.md inaccurate (moved or renamed files/classes, new conventions), update it in the same session.
