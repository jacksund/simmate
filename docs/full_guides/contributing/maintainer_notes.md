# Maintainer Guidelines

## Release Procedure

To generate a new release:

1. Modify the Simmate version number in `pyproject.toml` ([link](https://github.com/jacksund/simmate/blob/main/pyproject.toml))

2. Update the changelog with the new release and its release date.

3. Confirm all tests pass using the pre-built database. If they don't, generate a new one using the commands below, rename your db file (e.g., `prebuild-2022-07-05.sqlite3`), compress the db file into a zip file, upload it to the Simmate CDN, and modify the `archive_filename` in `simmate.database.utilites.load_default_sqlite3_build`.
``` bash
simmate database reset --confirm-delete --no-use-prebuilt
simmate database load-remote-archives
```

4. Generate a [release](https://github.com/jacksund/simmate/releases/new) on Github, which will automatically release to pypi.

5. For the conda release, wait for the autotick bot to initiate a pull request for the [simmate feedstock](https://github.com/conda-forge/simmate-feedstock). Check the status [here](https://conda-forge.org/status/#version_updates) (under "Queued").

6. Review the autotick bot's changes before merging. Changes to dependencies will likely require manual updates.

7. After merging, wait for the conda-forge channels to update their indexes (about 30 minutes). Then, test the conda install with:
``` bash
# for a normal release
conda create -n my_env -c conda-forge simmate -y
```

## Full Test Suite

Unit tests that require third-party programs (like VASP) are disabled by default. However, it's advisable to run a full test before new releases. To execute all unit tests that call programs like VASP:

1. Ensure you have the following prerequisites:
    - A Linux environment with VASP & Bader installed
    - Dev version of Simmate installed (`uv sync --all-extras`)
    - The `main` branch of the official repo checked out
    - Virtual environment is active (`source .venv/bin/activate`)
    - The base Simmate directory as the current working directory
    - Clear any custom `~/simmate` configs (i.e., ensure default settings)

2. Confirm the default test suite works:
``` bash
pytest
```

3. Reset your database, switch to the pre-built, and update it. This simulates the database of a new user:
```bash
simmate database reset --confirm-delete --use-prebuilt
simmate database update
```

4. Open `pyproject.toml` and modify the following line to run the VASP tests:
``` toml
# original line
addopts = "--no-migrations --durations=15 -m 'not blender and not vasp'"

# updated line
addopts = "--no-migrations --durations=15 -m 'not blender'"
```

5. (Optional) By default, all VASP tests run using `mpirun -n 12 vasp_std > vasp.out`. Modify this in `src/simmate/workflows/tests/test_all_workflow_runs.py` if needed.

6. Run `pytest` again to pick up these tests. It's advisable to run specific tests and enable logging (`-s`) for monitoring:
``` bash
# option 1
pytest

# option 2(recommended)
pytest src/simmate/workflows/test/test_all_workflow_runs.py -s
```

7. If all tests pass, proceed with the new release. Discard your changes afterwards.
