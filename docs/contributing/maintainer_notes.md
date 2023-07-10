
# Maintainer notes

!!! note
    currently this page is only relevant to @jacksund

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