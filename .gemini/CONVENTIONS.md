# Simmate Coding Conventions and Style

Adhere to these conventions to maintain consistency and compatibility within the Simmate ecosystem.

## 🐍 Python Style

- **Type Hints:** Required for all new functions and methods.
- **Imports:** Use absolute imports (`from simmate.toolkit import Structure`).
- **File Paths:** Always use `pathlib.Path` for file and directory manipulation.
- **Docstrings:** Use Google-style or clear standard Python docstrings.
- **Async/Sync:** Most scientific workflows and database operations are synchronous.

## 🗄️ Database and Models

- **Naming:** Database tables are typically PascalCase (e.g., `RelaxationRun`).
- **Inheritance:** Most models should inherit from `simmate.database.base_data_types.DatabaseTable`.
- **Conversion Methods:** 
    - `from_toolkit(...)`: Standard method to convert a toolkit object (like `Structure`) into a database entry.
    - `to_toolkit()`: Standard method to convert a database entry back into its toolkit object.
- **Mixins:** Use provided mixins in `simmate.database.base_data_types` (e.g., `SpacegroupMixin`) to avoid redundant field definitions.

## 🧪 Toolkit Objects

- **Immutability:** Treat `Structure`, `Molecule`, and `Composition` objects as mostly immutable. Operations that modify them should return a new object (patterned after Pymatgen/RDKit).
- **Initialization:** Use class methods like `from_file`, `from_dynamic_data`, or `from_dict`.

## 🚀 Workflows

- **Naming Convention:** Use `Type__App__Preset` for workflow class names (e.g., `Relaxation__Vasp__Matproj`). This naming should also be reflected in the registry path (e.g., `vasp/relaxation/matproj`).
- **Base Class:** Use `S3Workflow` for any workflow involving external software with file I/O, `StagedWorkflow` for multi-step runs, and `Workflow` for general orchestration.
- **Results:** Most workflows store their results in a database table that inherits from the `Calculation` mixin.

## ✅ Testing

- **Location:** Put tests in a `test/` subdirectory of the module you are testing.
- **Fixtures:** Use the fixtures in `src/simmate/conftest.py` (`structure`, `composition`, `sample_structures`).
- **Mocking:** Always mock external command calls and proprietary file access (like VASP's `POTCAR` files) unless specifically doing an integration test.
- **Cleanup:** Ensure all temporary files are written to the `tmp_path` or the `scratch_dir` provided by the test fixtures.
