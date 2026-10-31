# Maintainer Guidelines

## Release Procedure

To generate a new release:

1. Bump the version number in [`pyproject.toml`](https://github.com/jacksund/simmate/blob/main/pyproject.toml).

2. Add the new release and its date to the changelog.

3. Confirm all tests pass using the pre-built database. If they don't, generate a new one (`prebuild` saves a date-stamped zip, e.g. `prebuild-2022-07-05.zip`, to `~/simmate/sqlite-prebuilds/`). If only migrations have changed, start from the current prebuild:
    ``` bash
    simmate database reset --confirm-delete --use-prebuilt  # also applies new migrations
    simmate database prebuild
    ```
    To reload all third-party data instead:
    ``` bash
    simmate database reset --confirm-delete --no-use-prebuilt
    simmate database load <app_name>   # repeat for each app
    simmate database prebuild
    ```
    Then upload the newest zip to `sqlite-prebuilds/` on the Simmate CDN (requires `settings.s3` with write access) and update `archive_filename` in `simmate.database.utils.load_default_sqlite3_build`:
    ``` bash
    simmate database upload-prebuild
    ```

4. Create a [release](https://github.com/jacksund/simmate/releases/new) on GitHub, which automatically publishes to PyPI.

5. For the conda release, wait for the autotick bot to open a pull request on the [simmate feedstock](https://github.com/conda-forge/simmate-feedstock). Check its status [here](https://conda-forge.org/status/#version_updates) (under "Queued").

6. Review the autotick bot's changes before merging. Changes to dependencies will likely require manual updates.

7. After merging, wait for the conda-forge channels to update their indexes (about 30 minutes). Then, test the conda install:
    ``` bash
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

Tests that require third-party programs (like VASP) are skipped by default, but the full suite should be run before each release:

1. Prerequisites:
    - Linux with VASP and Bader installed
    - A [dev install](first_time_setup.md) with `main` checked out
    - Default settings (clear any custom `~/simmate` configs)

2. Confirm the default test suite passes:
    ``` bash
    simmate dev test
    ```

3. Reset to the pre-built database and update it. This simulates a new user's database:
    ``` bash
    simmate database reset --confirm-delete --use-prebuilt
    simmate database update
    ```

4. (Optional) VASP tests run with `mpirun -n 14 vasp_std > vasp.out` by default. Change this in `src/simmate/workflows/test/test_all_workflow_runs.py` if needed.

5. Run the full suite, which adds the VASP tests:
    ``` bash
    simmate dev test --full
    ```

    !!! tip
        To watch the VASP runs, run only the workflow tests with logging enabled:
        ``` bash
        pytest src/simmate/workflows/test/test_all_workflow_runs.py -s -m "not blender"
        ```

6. If all tests pass, continue with the release. Discard any edits from step 4.
