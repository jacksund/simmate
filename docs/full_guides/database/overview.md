# The Simmate Database

This module hosts everything for defining and interacting with your database.

For beginners, make sure you have completed [our database tutorial](https://jacksund.github.io/simmate/getting_started/access_the_database/quick_start/).

Submodules include...

- `base_data_types` : fundamental mix-ins for creating new tables
- `workflow_results` : collection of result tables for `simmate.workflows`
- `prototypes` : tables of prototype structures
- `third_parties` : loads data from external providers (such as Materials Project)

And there is one extra file in this module:

- `connect`: configures the database and installed apps (i.e. sets up Django)
