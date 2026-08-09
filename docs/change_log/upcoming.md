# Upcoming Release



!!! tip
    To view ongoing changes that haven't been finalized or merged yet, check our [active pull-requests](https://github.com/jacksund/simmate/pulls) on GitHub

**Enhancements**

- added `OnOff`, `TimeProportional`, and `FuzzyLogic` controllers, plus a `StirringHotPlate` device to `lab_automation` app, including an `.eval()` method and comprehensive documentation for sensors, controllers, and devices
- added create_prebuild function to database.utils for creating date-stamped SQLite3 database archives
- added the `simmate dev` command group with tools for linting, testing, and workspace management
- improved CLI help texts and added rich markdown support across all command groups
- update `cas_registry` app to use the official API as the primary backend and add a validation step to the chatbot lookup tool to verify cas
- improved `inventory_management` by adding Molecule and Structure tables for detailed substance tracking, linking substances to all other datasets, and beginning to build data explorer views
- added `StructureInput` and `htmx_structure_input` to standardize crystal structure loading across forms
- updated the OQMD data loading method to support the latest data provided by their team
- added draft of `accuracy_rating` to workflows to help beginners select the most appropriate settings
- added a `@schedule` decorator for easier periodic task registration
- added web components and templates for the pdb and chembl apps
- added crystalline dataset views to the Data Explorer, including 3D structure views, exports, and search forms
- added `@batch_bulk_create` decorator to help simplify `load_source_data` methods
- updated `simmate database download` to be dynamic across all apps, support a `--source` option, and respect custom load orders
- added first draft of vasp dockerfile. vasp is proprietary so source files and final image cannot be shared publicly
- added methods for updating rows and cleaning up chunk files to toolkit datastore class
- added parallel chunk loading to `MoleculeStore` datastores using UUID filenames, `reorganize_chunks`, and SLURM-compatible job submission via `SimmateExecutor`
- established working helm chart for k3s single-node deployment
- added web reports for static energy and relaxation calculations
- added plotly data streaming
- added base datastore class
- prototyped usearch vector db
- built out chemspace s3 datastore
- upgraded qe and evolution apps
- added qe sssp to docker images
- enabled update-many selection
- enabled updates for `@batch_bulk_create` decorator
- added a fork of `simple_pid`
- added an `on` keyword argument for weekly schedules

**Refactors**

- moved `simmate.workflows.execution` and `simmate.workflows.scheduler` to `simmate.compute` to align with the CLI and documentation structure
- renamed the `simmate engine` command group to `simmate compute` and updated internal modules/tests
- refactored `website.data_explorer` to use HTMX components for all table entries, moving UI-specific features from `DatabaseTable` and `HTMLMixin` into `DynamicTableForm`
- refactored the `chemspace` app to use an independent `ChemspaceClient` for source data management and chunked yielding, aligning its architecture with the `chembl` app
- moved `chemspace.utils.download_raw_files` into `ChemspaceClient.download_source_data`
- switched from ChemDoodle to Ketcher as the default molecule sketcher
- updated scheduler to submit tasks as `WorkItem`s instead of running them in-thread
- removed unused web templates and static assets
- updated envs for helm and docker-compose, where k3s is the top candidate for public production setups
- renamed the base component from `DynamicTableForm` to `TableComponent` and moved it to `simmate.website.data_explorer.components`. Standardized all app components
- cleaned up `simmate.dockerfile` by separating blender install and minimizing deps. Image is now <500mb
- rebuilt molecule datastore class
- adjusted s3 and datastore utils
- optimized chemspace repartitioning
- updated fingerprinting featurizers
- refactored staged workflows, docker builds, and gh ci
- updated chemspace s3 client
- updated chemspace datastore

**Fixes**

- patched connection contexts and closing in the `database.external_connectors` module
- fixed `htmx_molecule_input` for non-chemdraw sketcher
- fixed extra `$$$$` delimiter being written on bulk sdf export
- fixed typo in `volume_change` formula for relaxations
- patched data explorer entries context
- patched htmx forms and reports
- updated dask requirement to `<2026.3.1`
- bumped versions of various github actions in CI
- patched status tracking logic
- fixed project management mixin
- added missing CAS migration


