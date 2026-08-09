# Accessing Third-party Data

Simmate provides a set of **Data Apps** that simplify the process of downloading and querying data from external repositories. Instead of manually querying external APIs every time you run a script, these apps allow you to store the data locally in your Simmate database for lightning-fast access.

----------------------------------------------------------------------

## Supported Data Apps

For a full list of supported third-party datasets, please refer to the [Apps Overview](/apps/overview.md) page. This includes:

- **Crystal Structures**: Materials Project, OQMD, JARVIS, COD, and AFLOW.
- **Molecular Data**: BCPC, CAS Registry, ChEMBL, and more.

!!! tip
    The individual documentation for each app provides details on the data source, provider, and citation information.

----------------------------------------------------------------------

## Downloading Data (Remote Archives)

Downloading thousands (or millions) of entries through a REST API is often slow and inefficient. To solve this, Simmate uses **Remote Archives** — pre-packaged snapshots of these databases that can be downloaded and loaded in one step.

### From the Command Line
To download the archive for a specific app (e.g., Materials Project):
```shell
simmate database download materials_project
```

### In Python
You can also load the archive from within your script. This is especially useful for managing specific tables:

``` python
from simmate.database import connect
from simmate.apps.materials_project.models import MatprojStructure

# This will download the zip file, unpack it, and save all structures to your DB.
# WARNING: This can take >1 hour depending on the dataset size.
MatprojStructure.load_remote_archive()
```

!!! tip
    Once loaded, this data stays in your local database permanently. You only need to run this command once!

----------------------------------------------------------------------

## Updating Stability and Energy

Some data apps provide uncorrected energies. If you're using the `Thermodynamics` mix-in features (like `energy_above_hull`), you can update the stability information after loading the archive:

``` python
# Update stability for all structures in the table
MatprojStructure.update_all_stabilities()

# Update stability for a specific chemical system
MatprojStructure.update_chemical_system_stabilities("Y-C-F")
```

----------------------------------------------------------------------

## Why use Simmate Data Apps?

Unlike alternatives that query external APIs (like `MPRester` or `matminer`), Simmate Data Apps offer:

1. **Speed**: Loading data from your local database is hundreds of times faster than making web requests.
2. **Stability**: Your source data won't change unexpectedly in the middle of a study.
3. **Rich Querying**: Use the full power of the [Django ORM](./basic_use.md) to filter data by spacegroup, elements, density, and more.
4. **Integration**: Data is already in the Simmate format, ready to be used in workflows or with the Simmate Toolkit.
