# Simmate Project Context

Simmate is a full-stack framework for chemistry and materials science research. It provides tools for workflow management, database interaction (using Django), and a toolkit for scientific computing.

## Core Concepts

- **Apps:** Specialized modules for specific tools (e.g., VASP, Quantum Espresso), databases (e.g., Materials Project, AFLOW, ChEMBL, PubChem), or administrative tasks (e.g., Inventory Management, Project Management).
- **Toolkit:** Domain-specific objects like `Structure`, `Molecule`, `Composition`, `Spacegroup`, and utilities for symmetry, transformations, and featurization.
- **Database:** Django-based models for storing and querying crystal structures, molecular data, and workflow results.
- **Workflows:** Orchestrated sequences of computational tasks, often involving external software and database interactions.

## Key Technologies

- **Language:** Python 3.11 (specifically `>=3.11, <3.12`)
- **Web/DB Framework:** Django 5.2+ (with HTMX and Unicorn for dynamic UI)
- **CLI:** Typer (Primary entry point is `simmate`, with app-specific ones like `simmate-vasp`)
- **Scientific Libraries:** PyMatGen, ASE, RDKit, Pandas, NumPy, Matminer, Scikit-learn, LangChain (for AI agents)
- **Testing:** Pytest, Pytest-Django (Markers: `vasp`, `blender`, `pymatgen`, `slow`)
- **Documentation:** MkDocs with Material theme

## Development Standards

- **Type Hinting:** Use type hints for all new code.
- **Docstrings:** Follow Google-style docstrings or standard Python docstrings.
- **Testing:** New features must include tests in `src/simmate/*/test/`.
- **Database Migrations:** Django migrations are required for model changes.
- **Conventions:** 
    - Use `simmate.toolkit` objects (`Structure`, `Molecule`, `Composition`) for domain data.
    - Prefer Django ORM for all database operations.
    - CLI commands should be added to `simmate.command_line`.

## Workflow for AI Agent

- **Surgical Edits:** Favor `replace` for targeted changes in large files.
- **Testing:** Run `pytest` for validation. Many tests require specific environment setups (e.g., VASP, Blender), so use markers to skip if necessary.
- **Database:** Be aware of the `scratch_dir` pattern used in tests and workflows.
- **Dependencies:** Check `pyproject.toml` before assuming a library is available.
