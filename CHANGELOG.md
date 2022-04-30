# Release History

Our releases follow [semantic versioning](https://semver.org/). This means versions (e.g. `v1.2.3`) correspond to `MAJOR.MINOR.PATCH`. Each version number increases after the following changes:

  - `MAJOR` = incompatible API changes
  - `MINOR` = new functionality is added (w/o API changes)
  - `PATCH` = bug fixes and documentation updates (w/o API changes)

There is one key exception to the rules above -- and that is with `MAJOR`=0 releases. Any v0.x.y release is considered developmental where APIs are subject to change and should not be considered stable. This is consistent with the semantic version spec (see [point 4](https://semver.org/#spec-item-4)).


</br></br>


# Upcoming Release
> :bulb: for ongoing changes that have not been finalized/merged yet, view our [active pull-requests](https://github.com/jacksund/simmate/pulls) on github
- users can now apply their own unique keyword modifiers to Incars -- such as how we allow "__per_atom" or "__smart_ismear" tags on Incar settings. This change involved refactoring how `keyword_modifers` are implemented for the `vasp.inputs.Incar` class. Rather than static methods attached to the base class, modifiers are now dynamically applied using the `add_keyword_modifer` classmethod.
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
