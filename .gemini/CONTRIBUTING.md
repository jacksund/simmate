# Contributing to Simmate (AI-Specific Guide)

This guide is for adding new components to Simmate, focusing on the common patterns an AI agent should follow.

## Adding a New App

1.  **Create Directory:** New apps go into `src/simmate/apps/`.
2.  **`configs.py`:** Define the app's `AppConfig`. Register the app in `src/simmate/apps/configs.py`.
3.  **`models.py`:** Define Django models for the app. Inherit from `simmate.database.base_data_types.DatabaseTable` or `Calculation` where appropriate. Models can also be in a `models/` directory.
4.  **`workflows/`:** Define app-specific workflows in a `workflows/` directory. Ensure they are imported in `workflows/__init__.py` for automatic discovery.
5.  **`urls.py`:** If the app has a web interface, add a `urls.py` file to the app directory. Simmate's web UI automatically discovers and includes these.
6.  **Tests:** Create a `test/` directory within your app and add `test_*.py` files.

## Adding a New Workflow

1.  **Base Class:** Choose an appropriate base class from `simmate.workflows.base_flow_types`.
2.  **`run_config`:** Define the workflow's parameters and execution logic.
3.  **Registration:** Register the workflow in the app's `configs.py` or the global workflow registry.
4.  **CLI:** If it's a major workflow, expose it via a command in `src/simmate/command_line/`.

## Formatting and Linting

We use `black` for formatting and `isort` for import sorting. Run these before submitting any changes:

```bash
# From the project root
black .
isort .
```

## Testing Best Practices

- Use the fixtures in `src/simmate/conftest.py` (e.g., `structure`, `composition`, `sample_structures`).
- **Mocking:** Always mock external scientific codes (e.g., VASP, QE) unless explicitly doing an integration test. Use `mocker` and the helpers in `conftest.py`.
- **Cleanup:** Ensure tests clean up after themselves by using the `scratch_dir` pattern or `tmp_path`.
- **Running Tests:**
  ```bash
  # Run all tests (skipping environment-dependent ones)
  pytest -m "not vasp and not blender" --no-migrations
  ```
- New features must include tests in a `test/` directory within your app or module.
