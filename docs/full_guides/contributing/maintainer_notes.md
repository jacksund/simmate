# Maintainer Guidelines

## Release Procedure

To generate a new release:

1. Modify the Simmate version number in `pyproject.toml` ([link](https://github.com/jacksund/simmate/blob/main/pyproject.toml))

2. Update the changelog with the new release and its release date.

3. Confirm all tests pass using the pre-built database. If they don't, generate a new one using the commands below (`prebuild` saves a date-stamped zip, e.g. `prebuild-2022-07-05.zip`, to `~/simmate/sqlite-prebuilds/`), upload it to the Simmate CDN, and modify the `archive_filename` in `simmate.database.utils.load_default_sqlite3_build`.
``` bash
simmate database reset --confirm-delete --no-use-prebuilt
simmate database load <app_name>   # repeat for each app
simmate database prebuild
```

4. Generate a [release](https://github.com/jacksund/simmate/releases/new) on Github, which will automatically release to pypi.

5. For the conda release, wait for the autotick bot to initiate a pull request for the [simmate feedstock](https://github.com/conda-forge/simmate-feedstock). Check the status [here](https://conda-forge.org/status/#version_updates) (under "Queued").

6. Review the autotick bot's changes before merging. Changes to dependencies will likely require manual updates.

7. After merging, wait for the conda-forge channels to update their indexes (about 30 minutes). Then, test the conda install with:
``` bash
# for a normal release
conda create -n my_env -c conda-forge simmate -y
```

## Desktop App Builds

PyInstaller can only build for the OS it runs on, so the desktop app is built and uploaded separately on each OS. This requires `settings.s3` to be configured with write access to the Simmate CDN bucket. Uploads are named with the installed Simmate version, so update the version number (step 1 above) before building for a new release. On each machine:

``` bash
uv sync --all-extras
simmate desktop build
# launch dist/simmate-desktop (or dist/simmate-desktop.exe) to check it works
simmate desktop upload
```

Re-uploading the same version replaces that version's file. For example, the links for version 0.19.0 are:

- Windows: `https://assets.simmate.org/desktop/simmate-desktop-0.19.0-windows.exe`
- Linux: `https://assets.simmate.org/desktop/simmate-desktop-0.19.0-linux`
- macOS (untested): `https://assets.simmate.org/desktop/simmate-desktop-0.19.0-macos`

On startup, packaged apps compare their version to the latest GitHub release and offer to download the matching build from these links into `~/simmate/desktop/`. They only do so once that OS's build is uploaded, so upload builds for each OS soon after a release.

The builds are not code-signed, so Windows shows a SmartScreen warning ("More info → Run anyway") and macOS Gatekeeper blocks the app until it is allowed in *System Settings → Privacy & Security*.

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
