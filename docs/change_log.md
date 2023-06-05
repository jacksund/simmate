
--------------------------------------------------------------------------------

## Check your installed version

When you first import simmate and connect to the database, a warning is printed
if you are not using the most current version available. You can also check this in the command-line:

``` bash
simmate version
```

``` yaml
# example output
Installed version: v0.10.0
Newest available: v0.11.1
```

--------------------------------------------------------------------------------

## Updating to a newer version

We highly recommended that you install simmate into a clean conda environment, rather than updating simmate within your existing one:
``` shell
conda create -n my_env -c conda-forge python=3.11 simmate
```

Make sure you check that the expected version is now installed:
``` bash
simmate version
```

Rebuild your database with one compatible with the new installation:
``` bash
simmate database reset
```

!!! tip
    If you use the same environment name as an existing one, conda will ask if
    you'd like to delete the existing environment before creating the new one.
    This will save you time from having to delete the env in a separate command.

--------------------------------------------------------------------------------

## Version numbers & their meaning

Our releases follow [semantic versioning](https://semver.org/). This means versions (e.g. `v1.2.3`) correspond to `MAJOR.MINOR.PATCH`. Each version number increases after the following changes:

  - `MAJOR` = incompatible API changes
  - `MINOR` = new functionality is added (w/o API changes)
  - `PATCH` = bug fixes and documentation updates (w/o API changes)

There is one key exception to the rules above -- and that is with `MAJOR`=0 releases. Any v0.x.y release is considered developmental where APIs are subject to change and should not be considered stable. This is consistent with the semantic version spec (see [point 4](https://semver.org/#spec-item-4)).


--------------------------------------------------------------------------------


## Upcoming Release

!!! tip
    For ongoing changes that have not been finalized/merged yet, view our [active pull-requests](https://github.com/jacksund/simmate/pulls) on github

<!-- (hidden message for maintainer to use between releases)
- no new changes have been merged into the `main` branch yet
**Enhancements**
**Refactors**
**Fixes**
-->


**Enhancements**

- add `django-unicorn` to deps to enable dynamic fullstack web UIs
- add ChemDoodle js/css to website headers for use elsewhere
- add "Example Scripts" section to doc website with several new scripts
- many updates to the web UI to accomodate molecular datasets and workflows
- add `simmate engine` commands to help with tags and different queues
- add docs to help with simmate workers, clusters, and tagging
- add `simmate-vasp` command for common VASP utilities like testing config, plotting, and prepping inputs

**Refactors**

- VASP potcar references to "element mappings" is now standarized to "potcar mappings"
- refactor docs with new "Apps" section
- full refactor of `simmate engine` commands. many have been shortened/renamed

**Fixes**

- fix bug where hyphens aren't allowed in the database name
- fix guide for DO database setup
- fix incorrect evolutionary search imports
- hide pymatgen POTCAR warnings
- fix github CI bug for MacOS being unstable
- fix bug for zombie jobs causing evolutionary search to hang
- fix premature triggering of frozen error

--------------------------------------------------------------------------------

## v0.13.0 (2023.03.06)

**Enhancements**

- add `relax_bulk` and `relax_endpoints` parameters to optionally turn off pre-relaxations in NEB
- add CLEASE app for cluster expanison calculations (these workflows are highly experimental at the moment - so use with caution)
- update "bad-elf" workflow to accept an empty-atom template structure or a list
of empty sites
- add python 3.11 support
- `simmate database reset` now supports Postgres (requires admin user)
- docker images are now published to DockerHub and Github packages

**Refactors**

- `calculators` module is now the `apps` module and terminology is changed throughout the repo
- many dependencies are reworked to optional dependencies as all `apps` are now optional
- `workflow_engine` module has been renamed to `engine` to help shorten commands and import lines
- rework CI to use mamba instead of conda
- pull out dependencies for some apps that are now optional
- reorganize `Incar` class and move some functionality to general `utilities`
- NEB module is reorganized to help with building custom sets

**Fixes**

- fix site ordering in NEB supercell structures
- improve installation speed and guide users to conda alternatives like mamba
- clean up docs and fix several links
- apps are now registered to the web UI

!!! warning
    The refactoring of simmate "apps" led to many breaking changes in the python API.
    We strongly recommend clearing your `~/simmate/` directory, especially the
    `my_env-apps.yaml` file because app names have changed.

**0.13.1 (2023.03.11)**

- recover from `connection already closed` errors after long workflow runs
- fix bug where `simmate database reset` fails when there is no database `postgres` available
- update django regression of `django.db.backends.postgresql_psycopg2` to `django.db.backends.postgresql`
- fix bug where simmate cannot read vasp results due atypical number (e.g. -0.33328-312)
- fix bug where postgres cannot json serialize bs or dos results (int64 numbers)
- fix incorrect pointing of VASP potcars in matproj presets
- from `from_directory` method of the `Relaxation` database class
- fix HSE bandstructure and DOS kpoint file writing

**0.13.2 (2023.03.20)**

- fix pickling error for `workflow.run_cloud` command
- `simmate.website.third_parties` module is now the `data_explorer` module. With this, you can now specify custom database tables to appear in the "Data" section for the web UI

--------------------------------------------------------------------------------

## v0.12.0 (2022.10.23)

**Enhancements**

- add structure creators for `ASE`, `GASP`, `PyXtal`, `AIRSS`, `CALYPSO`, `USPEX`, and `XtalOpt` as well as documentation for creators.
- add `simmate version` command
- changelog and update guide added to documentation website
- add `show-stats`, `delete-finished`, and `delete-all` commands to `workflow-engine`
- add `Cluster` base class + commands that allow submitting a steady-state cluster via subprocesses or slurm
- add `started_at`, `created_at`, `total_time`, and `queue_time` columns to `Calculation` tables
- add `exlcude_from_archives` field to workflows to optionally delete files when compressing outputs to zip archives
- various improvements added for evolutionary search workflows, such as parameter optimization, new output files, and website views
- add `Fingerprint` database table and integrate it with `Fingerprint` validator
- support >2 element hull diargrams and complex chemical systems

**Refactors**

- optimize `get_series` method of `relaxation.vasp.staged`
- reorganize `selectors` module for evolutionary structure prediction

**Fixes**

- fix dynamic loading of toolkit structures from third-party databases
- fix race condition with workers and empty queues
- increases default query rate for `state.result()` to lessen database load

--------------------------------------------------------------------------------

## v0.11.0 (2022.09.10)

**Enhancements**

- REST API fields can now be specified directly with the `api_filters` attribute of any `DatabaseTable` class & fields from mix-ins are automatically added
- add `archive_fields` attribute that sets the "raw data" for the database table & fields from mix-ins are automatically added
- accept `TOML` input files in addition to `YAML`
- convergence plots and extras are now written for many workflow types (such as relaxations)
- when `use_database=True`, output files are automatically written and the workup method is directly paired with the database table.
- NEB workflow now accepts parameters to tune how distinct pathways are determined, including the max pathway length and cutoffs at 1D percolation.
- add `MatplotlibFigure` and `PlotlyFigure` classes to help with writing output files and also implementing these figures in the website UI
- update website to include workflow calculator types and add API links
- custom projects and database tables are now registered with Simmate and a intro guide has been added
- continued updates for `structure-prediction` workflows
- add inspection of methods for default input values and display them in metadata

**Refactors**

- the `website.core_components.filters` module has been absorbed into the `DatabaseTable` class/module
- yaml input for custom workflows now matches the python input format
- workup methods are largely depreciated and now database entries are returned when a workflow has `use_database=True`
- several NEB input parameters have been renamed to accurate depict their meaning.
- customized workflow runs now save in the original database table under the "-custom" workflow name
- `structure_string` column renamed to `structure` to simplify api logic
- clean up `toolkit.validators` module and establish fingerprint base class
- `calculators` and `workflows` modules are now based on simmate apps

**Fixes**

- fix bug in windows dev env where `simmate run-server` fails to find python path
- fix bug in `workflows explore` command where 'vasp' is the assumed calculator name
- fix broken example code in custom workflow docs
- fix broken website links and workflow views

**0.11.1 (2022.09.12)**

- fix transaction error with workers on a PostGres backend

--------------------------------------------------------------------------------

## v0.10.0 (2022.08.29)

**Enhancements**

- add NEB base classes to inherit from for making new subflows
- improve formatting of logging and cli using `typer` and `rich`
- cli now supports auto-completion to help with long commands
- add `convergence_limit` parameter to evolutionary search that works alongside `limit_best_survival`. This will absorb minor changes in energy with equivalent structures from prolonging the search.
- add `ExtremeSymmetry` transformation to attempt symmetry reduction on disordered structure
- account for structures in `fixed-composition` having fewer nsites than input becuase of symmetry reduction during relaxation. Also, add `min_structures_exact` parameter to ensure we have at least N structures with the expected number of sites
- add experimental `variable-composition` (variable refers to nsites, not stoichiometry) and `binary-composition` evolutionary searches
- allow custom workflows to run from yaml
- update MatProj data to new api, and add severl new columns for data (e.g. mag + band gap)

**Refactors**

- isolate optional dependencies so that our install is smaller
- remove click in favor of higher-level package (typer)
- `pre_standardize_structure` and `pre_sanitize_structure` functionality is now merged in to a `standardize_structure` parameter that accepts different mode. `symmetry_tolerance` and `angle_tolerance` parameters can also modify the symmetry analysis done.
- metadata files are now numbered to allow multiple metadata files in the same directory
- refactor & clean up transformation module for readability
- remove `SimmateFuture` class and merge functionality into `WorkItem`
- switch from pdoc to mkdocs for documentation and remove `get_doc_from_readme`. Code and doc organization are now decoupled.
- rename run commands based on user preference. the `run` is now `run-quick`. `run-yaml` is now `run`. `run-cloud` now assumes a yaml input.
- remove `tqdm` dependency in favor of `rich.progress`
- refactor transformations to static methods

**Fixes**

- fix `module not found` error by adding ASE to dependencies
- fix bug with postgres database trying to delete sqlite locally
- fix dask throwing errors with logging
- fix bug where `fixed-composition` searches fail to detect individuals that have been symmetrically reduced (and therefore have fewer nsites than expected)
- fix evolutionary search failures when writing output files while files are opened/locked
- fix NEB workflows failing due to Walltime handler
- fix NEB workflows hints for `workup` failure due to missing start/end image folders

--------------------------------------------------------------------------------

## v0.9.0 (2022.08.17)

**Enhancements**

- improve the warning associated with workflow failure because of "command not found" issues
- workers now ignore and reset tasks that fail with "command not found". 2 workers failing with this error will result in the WorkItem being canceled
- `RandomWySites` can now generate wyckoff combinations lazily (or up front) depending on use case
- add `simmate utilities` command group with `archive-old-runs`
- add `start-cluster` command for starting many local workers
- add `structure-prediction` workflows
- add plotting/output utilities to `EvolutionarySearch` and `relaxation.vasp.staged`


**Refactors**

- evolutionary search now delay creations, transformations, and validation until runtime (used to be at time of structure submission)
- `directory`, `compress_ouput`, and `run_id` are now default input parameters for subclasses of `Workflow`. If these are unused, the `run_config` must include `**kwargs`
- add `isort` for organizing module imports throughout package

**Fixes**

- fixed when `source` is not being registered by several workflows
- fix docker image for installing anaconda, blender, and simmate on ubuntu

--------------------------------------------------------------------------------

## v0.8.0 (2022.08.11)

**Enhancements**

- NEB workflows now accept parameters for changing supercell size and number of images used
- add HSE workflows for static energy, relaxation, and DOS/BS electronic states
- add NPT and MatProj molecular dynamics workflows
- add SCAN workflows for static energy and relaxation
- test files can be provided within zip files, fixing excessive line counts on git commits
- add simmate worker that can run "out-of-box" and requires no set up
- add logging for useful debugging and monitoring of workflows
- pinned dependencies to maximum versions and manage with dependabot


**Refactors**

- to simplify the creation of new workflows, `S3Task` is now `S3Workflow` and database tables are dynamically determined using the workflow name
- workflows of a given type (e.g. relaxation or static-energy) now share database tables in order to simplify overall database architecture
- migrate from `os.path` to `pathlib.Path` throughout package
- isolate prefect use to separate executors
- updated tutorials for new workflow engine and workers
- remove use of `setup.py` in favor of `pyproject.toml`

--------------------------------------------------------------------------------

## v0.7.0 (2022.07.19)

**Enhancements**

- add guide for installing VASP v5 to Ubuntu v22.04 ([@scott-materials](https://github.com/scott-materials), [#183](https://github.com/jacksund/simmate/issues/183))
- add `simmate database load-remote-archives` command and `load_remote_archives` utility that populates all tables from `database.third_parties`
- add `load_default_sqlite3_build` utility that downloads a pre-built database with all third-party data present. This is an alternative to calling `load_all_remote_archives` if you are using sqlite3 and saves a significant amount of time for users.
- standardize workflow naming. Note this breaks from python naming conventions for classes ([#150](https://github.com/jacksund/simmate/issues/150))
- dynamically determine `register_kwargs` and rename property to `parameters_to_register`
- add full-run unittests that call workflows and vasp (without emulation)
- add walltime error handler that properly shuts down calculations when a SLURM job is about to expire
- add option to restart workflows from a checkpoint
- automatically build api documentation using github actions

**Refactors**

- refactor `start-worker` command to use prefect instead of the experimental django executor
- remove experimental `workflow_engine.executor`
- move contents of `configuration.django.database` to `database.utilities`
- upgraded to Prefect v2 ("Orion"). This involved the refactoring the entire `workflow_engine` module, and therefore the entire workflow library. ([#185](https://github.com/jacksund/simmate/pull/185)).


**0.7.1 (2022.07.19)**

- fix incorrect handling of prefect v2 futures by workflows

**0.7.2 (2022.08.03)**

- fix missing SVG files for web UI ([#196](https://github.com/jacksund/simmate/pull/196)).

**0.7.3 (2022.08.04)**

- fix incorrect passing of `source` in NEB all-paths workflow causing it to fail

--------------------------------------------------------------------------------

## v0.6.0 (2022.06.25)

**Enhancements**

- add `AflowPrototypes` to the `database.third_parties` module (only includes data distributed through pymatgen)
- add new modules to `toolkit.structure_prediction` and `toolkit.creation`, including ones to provide `known`, `substitution`, and `prototype` based structures.
- add `created_at` and `updated_at` columns to all database tables
- check if there is a newer version of Simmate available and let the user know about the update
- add experimental `badelf` workflow for determining electride character
- add `electronic-structure` workflow which carries out both DOS and BS calculations
- add `database_obj` attribute to the `toolkit.Structure` base class that is dynamically set

**Refactors**

- standardize `database_table` attribute for workflows by merging `calculation_table` and `result_table` attributes ([#102](https://github.com/jacksund/simmate/issues/102))
- removed use of `-s`, `-c`, and `-d` shortcuts from the `workflows` commands
- refactor `relaxation/staged` workflow to run in single parent directory
- refactor evolutionary search algorithm (alpha feature)
- condense where parsing/deserialization of workflow parameters occurs to the refactored the `load_input_and_register` task. Originally, this would occur in multiple places (e.g. in the CLI module before submission, in the workflow run_cloud method, in the LoadInputAndRegister task, etc.) and involved boilerplate code. ([#173](https://github.com/jacksund/simmate/pull/173))
- refactor experimental features `register_kwargs` and `customized` workflows
- refactor `LoadInputAndRegister` and `SaveOutputTask` to `load_input_and_register` and `save_result`

**Fixes**

- fix import for `visualization.structure.blender` module ([@bocklund](https://github.com/bocklund), [#180](https://github.com/jacksund/simmate/issues/180))
- fix bug where `command` or `directory` improperly passes `None` when they are not set in the `simmate workflows run` command
- fix bug where `update_all_stabilities` grabs incomplete calculations ([#177](https://github.com/jacksund/simmate/pull/177))
- fix bug where SCF calculation is not completed before the non-SCF DOS or BS calculation and causes the workflows to fail ([#171](https://github.com/jacksund/simmate/issues/171))
- fix bug for Bader workflow by registering the prebader workflow ([#174](https://github.com/jacksund/simmate/pull/174))
- fix bug where `source` is not determined with yaml-file submissions ([#172](https://github.com/jacksund/simmate/issues/172))

--------------------------------------------------------------------------------

## v0.5.0 (2022.05.30)
- update CI to test all OSs and pin pytest<7.1 as temporary fix for [#162](https://github.com/jacksund/simmate/issues/162)
- fix spelling typos in `keyword_modifiers` ([@laurenmm](https://github.com/laurenmm), [#165](https://github.com/jacksund/simmate/pull/165))
- users can now apply their own unique keyword modifiers to Incars -- such as how we allow "__per_atom" or "__smart_ismear" tags on Incar settings. This change involved refactoring how `keyword_modifiers` are implemented for the `vasp.inputs.Incar` class. Rather than static methods attached to the base class, modifiers are now dynamically applied using the `add_keyword_modifier` classmethod.
- large update of `calculators.vasp.tasks` module where many new presets are reimplemented from [`pymatgen.io.vasp.sets`](https://pymatgen.org/pymatgen.io.vasp.sets.html). This includes robust unit testing to confirm that generated inputs match between simmate and pymatgen (see [#157](https://github.com/jacksund/simmate/issues/157) for a list of presets)
- catch error with vasp freezing when `Brmix` handler switches to kerker mixing ([@becca9835](https://github.com/becca9835), [#159](https://github.com/jacksund/simmate/issues/159))

--------------------------------------------------------------------------------

## v0.4.0 (2022.04.24)
- add `description_doc_short` + `show_parameters` to workflows and use these to update the UI
- add django-allauth dependency for account management and google/github sign-ins
- archive directory as `simmate_attempt_01.zip` whenever an error handler is triggered
- depreciate the workflow parameter `use_prev_directory` in favor of `copy_previous_directory`

--------------------------------------------------------------------------------

## v0.3.0 (2022.04.19)
- add highly customizable VASP workflow
- add Bader analysis and ELF workflows
- update module readmes to warn of experimental features
- reorganize `toolkit` module

--------------------------------------------------------------------------------

## v0.2.0 (2022.04.15)
- start the CHANGELOG!
- refactor API views and add `SimmateAPIViewSet` class
- refactor `simmate start-project` command and underlying methods
- refactor `simmate workflow-engine run-cluster` command and underlying methods
- continue outlining `file_converters` module

--------------------------------------------------------------------------------

## v0.1.4 (2022.04.12)
- web interface styling
- minor bug fixes

--------------------------------------------------------------------------------

## v0.0.0 (2022.03.28)
- initial release
- adding tests and docs

--------------------------------------------------------------------------------
