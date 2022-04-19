# Release History

Our releases follow [semantic versioning](https://semver.org/). This means versions (e.g. `v1.2.3`) correspond to `MAJOR.MINOR.PATCH`. Each version number increases after the following changes:

  - `MAJOR` = incompatible API changes
  - `MINOR` = new functionality is added (w/o API changes)
  - `PATCH` = bug fixes and documentation updates (w/o API changes)

There is one key exception to the rules above -- and that is with `MAJOR`=0 releases. Any v0.x.y release is considered developmental where APIs are subject to change and should not be considered stable. This is consistent with the semantic version spec (see [point 4](https://semver.org/#spec-item-4)).

</br></br>

# Upcoming Release
- No new features merged into `main` yet


# v0.3.0
- add highly customizable VASP workflow
- add Bader analysis and ELF workflows
- update module readmes to warn of experimental features
- reorganize `toolkit` module


# v0.2.0
- start the CHANGELOG!
- refactor API views and add `SimmateAPIViewSet` class
- refactor `simmate start-project` command and underlying methods
- refactor `simmate workflow-engine run-cluster` command and underlying methods
- continue outlining `file_converters` module


# v0.0.0 - v0.1.4
- initial release
- web interface styling
- minor bug fixes
- adding tests and docs
