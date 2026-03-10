# Simmate Database Architecture

Simmate uses the Django Object-Relational Mapper (ORM) for all database operations, ensuring a structured and queryable way to manage chemical and materials data.

## Key Model Types

- **`DatabaseTable` (Custom Mixin):** Many models inherit from `simmate.database.base_data_types.DatabaseTable`. This often includes methods like `from_toolkit()` and `to_toolkit()` for converting between Django models and domain-specific `toolkit` objects (e.g., `Structure`, `Molecule`).
- **`Calculation` (Custom Mixin):** Extends `DatabaseTable` to include workflow-specific metadata like `run_id`, `status`, and timestamps.
- **`SearchResults` (Custom QuerySet):** Overrides the default Django manager to provide methods like `to_toolkit()`, `to_dataframe()`, and `to_archive()` for easier scientific data manipulation.
- **`Structure`, `Composition`, and `Molecule` Models:** Base types for materials and molecular data. `Structure` and `Composition` are in the core database, while `Molecule` is often used via the `rdkit` app.
- **`StatusTracking` (Custom Mixin):** Provides fields for tracking progress and errors in long-running tasks.

## Common Operations

- **Querying:** Standard Django `QuerySet` API. Example: `MyModel.objects.filter(chemical_system="Fe-O").all()`.
- **Conversions:** Always prefer the `from_toolkit` and `to_toolkit` methods if they exist.
- **Migrations:** Changes to models in `apps/` or `database/` require running `simmate db make-migrations` (or the equivalent Django command).

## External Connectors

Located in `src/simmate/database/external_connectors/`. These are specialized models/utilities for interacting with third-party databases (e.g., Materials Project, AFLOW, Jarvis).

## Data Integrity

The `simmate.database.utilities` module contains helpers for connecting to different database backends (SQLite, PostgreSQL) and loading initial data.
