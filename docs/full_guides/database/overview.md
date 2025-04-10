# Simmate Database Module

This module provides tools for defining and managing your database.

If you're new to this, make sure you've gone through [our database tutorial](/getting_started/database/quick_start.md).

The module includes the following submodules:

- `base_data_types` : Fundamental mix-ins for creating new tables
- `workflow_results` : A set of result tables for `simmate.workflows`
- `prototypes` : Tables that hold prototype structures
- `third_parties` : Tables derived from external sources (like Materials Project)

In addition, this module includes an extra file:

- `connect`: This file sets up the database and installed apps (in other words, it configures Django)