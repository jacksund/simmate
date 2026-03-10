# Simmate Project Structure and Organization

This document provides a detailed map of the Simmate repository to help you locate relevant scripts, modules, and functionalities.

## 📂 Core Package: `src/simmate/`

The heart of the project, organized by high-level responsibility.

### 🧩 `apps/` - Specialized Modules
Contains integrations for external software (VASP, Quantum Espresso) and third-party databases. All apps are registered in `src/simmate/apps/configs.py`.
- **Common Structure:**
    - `models.py` or `models/`: Database tables. Optional if using standard base types.
    - `workflows/`: App-specific workflows. Must be imported in `__init__.py`.
    - `inputs/` and `outputs/`: File I/O utilities for specific tools.
    - `urls.py`: Web UI routes (optional, discovered automatically).
    - `command_line/`: Custom CLI commands.

### 🧪 `toolkit/` - Scientific Logic
Domain-specific objects and algorithms that don't depend on the database.
- **`base_data_types/`**: Core objects like `Structure`, `Molecule`, `Composition`, and `Reaction`.
- **`symmetry/`**: Symmetry analysis tools (spacegroups, point groups).
- **`transformations/`**: Logic for modifying structures (e.g., creating supercells, adding vacancies).
- **`validators/`**: Checks for structure quality or convergence.
- **`visualization/`**: Helpers for plotting and 3D rendering.

### 🗄️ `database/` - Data Management
Infrastructure for the Django-based database.
- **`base_data_types/`**: Generic database models used across apps (e.g., `Relaxation`, `StaticEnergy`, `Calculation`).
- **`workflow_results/`**: Base models and mixins for logging workflow metadata.
- **`external_connectors/`**: Scripts for fetching data from external APIs (AFLOW, Jarvis, etc.).
- **`utilities.py`**: Key functions for initializing and connecting to the database.

### ⚙️ `workflows/` - Orchestration
The engine for running and managing computational tasks.
- **`base_flow_types/`**: Base classes (`Workflow`, `S3Workflow`, `StagedWorkflow`) that define execution patterns.
- **`execution/`**: Backend logic for how tasks are submitted and monitored.
- **`error_handler.py`**: Framework for handling software-specific errors (e.g., VASP crashes).
- **`scheduler.py`**: Logic for managing queued tasks.

### 💻 `command_line/` - CLI Interface
Defines the `simmate` command and its subcommands.
- **`base_command.py`**: The entry point for the Typer app.
- **`database.py`**: Commands for DB migrations and setup (`simmate db ...`).
- **`workflows.py`**: Commands for listing and running workflows (`simmate workflows ...`).
- **`config.py`**: Commands for local configuration (`simmate config ...`).

### 🌐 `website/` - Web Interface
The Django-based web application.
- **`core/`**: Main Django site configuration.
- **`data_explorer/`**: Views and templates for browsing the database.
- **`core_components/`**: Shared templates and static files.
- **`htmx/` and `unicorn/`**: Modern Django components for reactive UI.
- **`workflows/`**: Web views for triggering and monitoring workflows.
- **`user_tracking/`**: Logic for monitoring user activity and usage.

---

## 🛠️ Common Script Locations

Use this as a quick reference for where to search or add new logic:

| Feature | Directory |
| :--- | :--- |
| **New Scientific Algorithm** | `src/simmate/toolkit/` |
| **External Software Wrapper** | `src/simmate/apps/` |
| **Database Schema Change** | `src/simmate/apps/` (in `models.py`) |
| **Workflow Run Logic** | `src/simmate/workflows/` or `src/simmate/apps/*/workflows/` |
| **CLI Subcommand** | `src/simmate/command_line/` |
| **File I/O Utility** | `src/simmate/utilities/` or `src/simmate/toolkit/file_converters/` |
| **New Test Case** | Within a `test/` folder inside the relevant module |

---

## 🌲 Directory Tree (Simplified)

```text
simmate/
├── docs/                      # Documentation (MkDocs)
├── envs/                      # Deployment/Docker configs
├── src/
│   └── simmate/
│       ├── apps/              # VASP, QE, Materials Project, etc.
│       ├── command_line/      # CLI entry points
│       ├── configuration/     # Django settings
│       ├── database/          # DB utilities and mixins
│       ├── toolkit/           # Scientific objects/algorithms
│       ├── utilities/         # General helpers
│       ├── website/           # Django UI
│       └── workflows/         # Execution engine
├── pyproject.toml             # Dependencies and build info
└── README.md
```
