# Release History

Our releases follow [semantic versioning](https://semver.org/). This means versions (e.g. `v1.2.3`) correspond to `MAJOR.MINOR.PATCH`. Each version number increases after the following changes:

  - `MAJOR` = incompatible API changes
  - `MINOR` = new functionality is added (w/o API changes)
  - `PATCH` = bug fixes and documentation updates (w/o API changes)

There is one key exception to the rules above -- and that is with `MAJOR`=0 releases. Any v0.x.y release is considered developmental where APIs are subject to change and should not be considered stable. This is consistent with the semantic version spec (see [point 4](https://semver.org/#spec-item-4)).


</br></br>


# Upcoming Release
> :bulb: For ongoing changes that have not been finalized/merged yet, view our [active pull-requests](https://github.com/jacksund/simmate/pulls) on github

<!-- (hidden message for maintainer to use between releases)
- no new changes have been merged into the `main` branch yet
**Enhancements**
**Refactors**
**Fixes**
-->

**Enhancements**
- improve the warning associated with workflow failure because of "command not found" issues
- workers now ignore and reset tasks that fail with "command not found". 2 workers failing with this error will result in the WorkItem being canceled
- `RandomWySites` can now generate wyckoff combinations lazily (or up front) depending on use case
- add `simmate utilities` command group with `archive-old-runs`
- add `start-cluster` command for starting many local workers
- add `structure-prediction` workflows


**Refactors**
- evolutionary search now delay creations, transformations, and validation until runtime (used to be at time of structure submission)
- `directory`, `compress_ouput`, and `run_id` are now default input parameters for subclasses of `Workflow`. If these are unused, the `run_config` must include `**kwargs`



# v0.8.0 (2022.08.11)

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



# v0.7.0 - v0.7.3 (2022.07.19 - 2022.08.04)

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

**Fixes**
- fix incorrect passing of `source` in NEB all-paths workflow causing it to fail
- fix missing SVG files for web UI ([#196](https://github.com/jacksund/simmate/pull/196)).
- fix incorrect handling of prefect v2 futures by workflows



# v0.6.0 (2022.06.25)

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



# v0.5.0 (2022.05.30)
- update CI to test all OSs and pin pytest<7.1 as temporary fix for [#162](https://github.com/jacksund/simmate/issues/162)
- fix spelling typos in `keyword_modifiers` ([@laurenmm](https://github.com/laurenmm), [#165](https://github.com/jacksund/simmate/pull/165))
- users can now apply their own unique keyword modifiers to Incars -- such as how we allow "__per_atom" or "__smart_ismear" tags on Incar settings. This change involved refactoring how `keyword_modifiers` are implemented for the `vasp.inputs.Incar` class. Rather than static methods attached to the base class, modifiers are now dynamically applied using the `add_keyword_modifier` classmethod.
- large update of `calculators.vasp.tasks` module where many new presets are reimplemented from [`pymatgen.io.vasp.sets`](https://pymatgen.org/pymatgen.io.vasp.sets.html). This includes robust unit testing to confirm that generated inputs match between simmate and pymatgen (see [#157](https://github.com/jacksund/simmate/issues/157) for a list of presets)
- catch error with vasp freezing when `Brmix` handler switches to kerker mixing ([@becca9835](https://github.com/becca9835), [#159](https://github.com/jacksund/simmate/issues/159))



# v0.4.0 (2022.04.24)
- add `description_doc_short` + `show_parameters` to workflows and use these to update the UI
- add django-allauth dependency for account management and google/github sign-ins
- archive directory as `simmate_attempt_01.zip` whenever an error handler is triggered
- depreciate the workflow parameter `use_prev_directory` in favor of `copy_previous_directory`



# v0.3.0 (2022.04.19)
- add highly customizable VASP workflow
- add Bader analysis and ELF workflows
- update module readmes to warn of experimental features
- reorganize `toolkit` module



# v0.2.0 (2022.04.15)
- start the CHANGELOG!
- refactor API views and add `SimmateAPIViewSet` class
- refactor `simmate start-project` command and underlying methods
- refactor `simmate workflow-engine run-cluster` command and underlying methods
- continue outlining `file_converters` module



# v0.0.0 - v0.1.4 (2022.03.28 - 2022.04.12)
- initial release
- web interface styling
- minor bug fixes
- adding tests and docs
