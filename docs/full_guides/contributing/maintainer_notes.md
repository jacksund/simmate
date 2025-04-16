# Maintainer Guidelines

## Release Procedure

To generate a new release, adhere to these steps:

1. Modify the Simmate version number in `pyproject.toml` ([link](https://github.com/jacksund/simmate/blob/main/pyproject.toml))

2. Update the changelog with the new release and its release date.

3. Confirm all tests pass using the pre-built database. If they don't, generate a new one using the commands below, rename your db file (e.g., `prebuild-2022-07-05.sqlite3`), compress the db file into a zip file, upload it to the Simmate CDN, and modify the `archive_filename` in `simmate.database.utilites.load_default_sqlite3_build`.
``` bash
simmate database reset --confirm-delete --no-use-prebuilt
simmate database load-remote-archives
```

4. Generate a [release](https://github.com/jacksund/simmate/releases/new) on Github, which will automatically release to pypi.

5. Wait for the autotick bot to initiate a pull request for the [simmate feedstock](https://github.com/conda-forge/simmate-feedstock). Check the status [here](https://conda-forge.org/status/#version_updates) (under "Queued").

6. Review the autotick bot's changes before merging. If there were substantial changes, use [grayskull](https://github.com/conda-incubator/grayskull) to modify the version number, sha256, and dependencies.

7. After merging, wait for the conda-forge channels to update their indexes (about 30 minutes). Then, test the conda install with:
``` bash
# for a normal release
conda create -n my_env -c conda-forge simmate -y

# additionally, ensure spyder can also be installed in the same environment
conda install -n my_env -c conda-forge spyder -y
```

## Full Test Suite

Unit tests that require third-party programs (like VASP) are disabled by default. However, it's advisable to run a full test before new releases. To execute all unit tests that call programs like VASP:

1. Ensure you have the following prerequisites:
      - A Linux environment with VASP & Bader installed
      - Dev version of Simmate installed
      - The `main` branch of the official repo checked out
      - `simmate_dev` environment is active
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

## Website CSS

The Hyper theme, as outlined in our main docs [here](/full_guides/website/setup_and_config.md#css-and-js-assets), must be built and hosted separately from any Simmate server due to licensing. To build/host the assets, adhere to these steps: 

1. Download the Hyper theme (private access): e.g., `Hyper_v4.6.0.zip`
2. Unpack the zip file and navigate to this directory:
``` bash
cd Hyper_v4.6.0/Bootstrap_5x/Hyper/
```
3. Install prerequisites into a new conda environment and activate it:
``` bash
conda create -n hyper -c conda-forge nodejs yarn git
conda activate hyper
```
4. Install gulp using npm (conda install of gulp doesn't work):
``` bash
npm install gulp -g
```
5. In the main directory, install all Hyper dependencies using the `yarn.lock` file:
``` bash
yarn install
```
6. Edit themes/colors in the following files (e.g., change primary to `#0072ce`):
```
/src/assests/scss/config/saas/
>> go into each folder's _variables.scss
```
7. Build the assets:
``` bash
gulp build
```
8. Upload assets (in `dist` folder) to your CDN for serving.