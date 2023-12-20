
# Maintainer notes

## Making a release

To make a new release, you must follow these steps:

1. Update the Simmate version number in `pyproject.toml` ([here](https://github.com/jacksund/simmate/blob/main/pyproject.toml))

2. Update the changelog with the new release and date

3. Ensure all tests pass when using the pre-built database. Otherwise, you need to (i) make a new one using the commands below, (ii) rename your db file to something like `prebuild-2022-07-05.sqlite3`, (iii) compress the db file to a zip file, (iv) upload it to the Simmate CDN, and (iii) update the `archive_filename` in `simmate.database.third_parties.utilites.load_default_sqlite3_build`.
``` bash
simmate database reset --confirm-delete --no-use-prebuilt
simmate database load-remote-archives
```

4. Make a [release](https://github.com/jacksund/simmate/releases/new) on Github (which will automatically release to pypi)

5. Wait for the autotick bot to open a pull request for the [simmate feedstock](https://github.com/conda-forge/simmate-feedstock). This can take up to 24hrs, but you can check the status [here](https://conda-forge.org/status/#version_updates) (under "Queued").

6. Make sure the autotick bot made the proper changes before merging. If there were any major changes, you can use [grayskull](https://github.com/conda-incubator/grayskull) to help update the version number, sha256, and dependencies.

7. After merging, it takes the conda-forge channels 30min or so to update their indexes. Afterwards, you can test the conda install with:
``` bash
# for a normal release
conda create -n my_env -c conda-forge simmate -y

# as an extra, make sure spyder can also be installed in the same env
conda install -n my_env -c conda-forge spyder -y
```

## The full test suite

Unit tests that require third-party programs (such as VASP) are disabled by default. While there are tests that "mock" program behavior, it is still best to run a full test before making new releases. To run all unit tests that actually call programs like VASP:

1. Make sure you have the following prerequisites:
   - a linux env with VASP & Bader installed
   - dev version of simmate installed
   - the `main` branch of the official repo checked out
   - `simmate_dev` env is active
   - the base simmate directory as the current working directory
   - clear any custom `~/simmate` configs (i.e. make sure we have defaults)

2. Make sure the default test suite works:
``` bash
pytest
```

1. Reset your database, switch to the pre-built, and make sure it's up to date. We do this to mimic the database of a brand new user:
```bash
simmate database reset --confirm-delete --use-prebuilt
simmate database update
```

1. Open `pyproject.toml` and find the following line:
``` toml
addopts = "--no-migrations --durations=15 -m 'not blender and not vasp'"
```

1. This line contains the default options when calling `pytest`. You can see how `not vasp` is included to skip tests that require VASP. Let's modify this line such that the VASP tests do in fact run:
``` toml
addopts = "--no-migrations --durations=15 -m 'not blender'"
```

1. save the `pyproject.toml` -- but remember that you changed it! You will undo these changes later.

2. (optional) By default, all VASP tests will run using `mpirun -n 12 vasp_std > vasp.out`. You can update this in the file `src/simmate/workflows/tests/test_all_workflow_runs.py` if you would like to. There are multiple places where this is defined -- so make sure you read the entire script!

3. Now run `pytest` again where it will now pick up these tests. Note, we may only want to run specific test AND enable logging (`-s`) for them so that we can monitor -- both are optional but recommended:
``` bash
# option 1
pytest

# option 2(recommended)
pytest src/simmate/workflows/test/test_all_workflow_runs.py -s
```

9. If everything worked, then we can make a new release! Feel free to discard your changes


## Website CSS

The Hyper theme described in our main docs [here](/simmate/full_guides/website/overview/#css-and-js-assets) must be built and hosted separately from any Simmate
server to abide by licensing. The build/host the assests, follow these steps: 


1. download hyper theme (private access): e.g. `Hyper_v4.6.0.zip`
2. unpack the zip file and navigate to this directory:
``` bash
cd Hyper_v4.6.0/Bootstrap_5x/Hyper/
```
3. install prereqs into a new conda env and activate it
``` bash
conda create -n hyper -c conda-forge nodejs yarn git
conda activate hyper
```
4. install gulp using npm (conda install of gulp doesn't work)
``` bash
npm install gulp -g
```
5. in the main dir, install all hyper dependencies using the `yarn.lock` file
``` bash
yarn install
```
6. edit any themes/colors in the following files (e.g. change primary to `#0072ce`)
```
/src/assests/scss/config/saas/
>> go into each folder's _variables.scss
```
7. Build the assets
``` bash
gulp build
```
8. Upload assests (in `dist` folder) to your cdn for serving