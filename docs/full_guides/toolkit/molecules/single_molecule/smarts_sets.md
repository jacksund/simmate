# SMARTS Sets

--------------------------------------------------------------------------------

## Overview :pencil:

SMARTS queries are used for substructure searches and identifying functional groups. This module offers "sets" of common substructures and functional groups, which can be used to label molecules.

The `SmartsSet` class manages the search and labeling process for input molecules.

--------------------------------------------------------------------------------

## Available Sets :toolbox:

Two default SMARTS sets are available:

- `ChemblAlerts` ([csv](#UPDATE TO GITHUB LINK))
- `CdkFunctionalGroups` ([csv](#UPDATE TO GITHUB LINK))

The `ChemblAlerts` set includes several popular subsets:

- Glaxo
- Dundee
- BMS
- PAINS
- MLSMR

--------------------------------------------------------------------------------

## Basic Usage :hammer:

### Accessing a Set's Data 

You can access the original raw data (from a CSV file) and a column for SMARTS `Molecule` objects using the `smarts_data` and `smarts_dict` class properties.

For instance, using `ChemblAlerts`:

```python
from simmate.toolkit.smarts_sets import ChemblAlerts

# option 1 (as pandas.DataFrame)
data = ChemblAlerts.smarts_data

# option 2 (as dict)
data = ChemblAlerts.smarts_dict
```

### Counting Matches

To obtain the exact count of each functional group, use `get_counts`:

``` python
from simmate.toolkit.smarts_sets import ChemblAlerts

matches = ChemblAlerts.get_counts(
    molecule,
    include_misses=False,
)
```

### Listing Matches

If you only need a list of the SMARTS that matched, rather than exact counts, use `get_matches`:

``` python
from simmate.toolkit.smarts_sets import ChemblAlerts

matches = ChemblAlerts.get_matches(molecule)
```

--------------------------------------------------------------------------------

## Parallelization :gear:

!!! warning
    The parallelization method for this class is not yet available. Please contact us if you require this feature.

--------------------------------------------------------------------------------

## Adding a New Set

To add a new SMARTS set, you need to:

1. Create a csv file with `name` and `smarts_str` columns (you can add more columns if needed)
2. Inherit from the `SmartsSet` base class
3. Specify the location of the CSV file with the `source_file` attribute

The `SmartsSet` will then manage the behavior of `get_counts` and other features.

For example:

``` python
from simmate.toolkit.smarts_sets.base import SmartsSet


class CustomAlerts(SmartsSet):
    source_file = "path/to/custom_alerts.csv"
```

--------------------------------------------------------------------------------