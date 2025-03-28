
# The BadELF App

!!! note
    The current maintainer of this application is [Sam Weaver](https://github.com/SWeav02)

    The BadELF algorithm and application are based on the following research:
    
    - ["Counting Electrons in Electrides"](https://pubs.acs.org/doi/abs/10.1021/jacs.3c10876) (JACS 2023)
    - ["Assessing Dimensionality in Electrides"](https://pubs.acs.org/doi/10.1021/acs.jpcc.4c06803) (JPCC 2025)
    
--------------------------------------------------------------------------------

## About

BadELF is a method that combines Bader Charge Analysis and the Electron Localization Function (ELF) to predict oxidation states and perform population analysis of electrides. It uses Bader segmentation of the ELF to calculate the charge on electride electrons and Voronoi segmentation of the ELF to calculate charge on atoms. Since the original BadELF paper was published, additional functionality has been added to handle systems with covalent/metallic features and for handling the up/down spin ELF and charge density separately.

Simmate's BadELF application provides workflows and utilities to streamline BadELF analysis. This page provides a summary of how to run the BadELF algorithm. For more details and advanced usage, see the BadElfToolkit and ElectrideFinder docs. 

!!! note
    BadELF currently only works with VASP, but we are interested in expanding its use to other ab initio software. If you are interested in this, let us know, as that will help to make this a higher priority.

--------------------------------------------------------------------------------

## Installation

To use the BadELF module you will first need to follow the instructions for [installing simmate](../../../getting_started/installation/quick_start.md). Then BadELF can be set up with the following instructions.

1. This app uses `pybader` under the hood. Install this with:
``` bash
conda install -n my_env -c conda-forge pybader
```

2. Add `badelf` (and it's dependencies) to the list of installed Simmate apps with:
``` bash
simmate config add badelf
```

3. Update your database to include custom tables from the `badelf` app:
``` shell
simmate database update
```

4. Ensure everything is configured correctly:
``` shell
simmate config test badelf
```

--------------------------------------------------------------------------------

## Basic Use

BadELF requires outputs from VASP calculations (e.g. the CHGCAR, ELFCAR, etc.). You can either (a) generate these on your own or (b) run a simmate workflow that does it for you. 

### (a) from VASP outputs

The BadELF algorithm can be run in a folder with VASP results. Please ensure your VASP settings generate a CHGCAR and ELFCAR with matching grid sizes. 

Create a yaml file:
``` yaml
# inside input.yaml
workflow_name: bad-elf.badelf.badelf
directory: /path/to/folder

# all parameters below are optional
find_electrides: true # Whether or not to use ElectrideFinder to automatically find electrides
labeled_structure_up: none # If find_electrides is false, a labeled structure with dummy atoms (see ElectrideFinder docs)
labeled_structure_down: none # Same as above, but for spin down system
electride_finder_kwargs: # Settings for the ElectrideFinder. See ElectrideFinder docs for more info
    resolution: 0.02,
    include_lone_pairs: false,
    metal_depth_cutoff: 0.1,
    min_covalent_angle: 135,
    min_covalent_bond_ratio: 0.35,
    shell_depth: 0.05,
    electride_elf_min: 0.5,
    electride_depth_min: 0.2,
    electride_charge_min: 0.5,
    electride_volume_min: 10,
    electride_radius_min: 0.3,
algorithm: badelf # The algorithm for separating atoms and electride sites
separate_spin: true # Whether to treat spin-up and spin-down systems separately
shared_feature_algorithm: zero-flux # The algorithm for separating covalent/metallic features
ignore_low_pseudopotentials: false # Forces algorithm to ignore errors related to PPs with few electrons
write_electride_files: false # Writes the bare electron volume ELF and charge
write_ion_radii: true # Writes the ionic radius calculated from the ELF for each atom
write_labeled_structure: true # Writes a cif file with dummy atoms for each non-atomic ELF feature
```

And run the workflow:
``` bash
simmate workflows run input.yaml
```

Alternatively, the BadELF algorithm can be run from the command line without a yaml file:
``` bash
simmate workflows run-quick bad-elf.badelf.badelf --directory /path/to/folder
```

For a complete list of parameters, see our [parameters page](../../parameters)

### (b) from structure

If you would prefer to have Simmate handle the VASP calculation, workflows are available that will first run the required DFT and then BadELF. 

These workflows are stored in the `Warren Lab` app, which contains our lab's preferred VASP settings. Refer to the `Warren Lab` app for more details and to view the available workflows.

--------------------------------------------------------------------------------

## Viewing Results

Running BadELF using a .yaml file or the command line uses Simmate's Workflow system. The results of these workflows can be viewed in a couple of ways.

### (1) The Database

When setting up simmate, you should have created a local or cloud database. Results from any workflow run through simmate will be stored here, allowing for the automation of high-throughput calculations. Basic usage of the database can be found in our [docs](../../getting_started/database/quick_start). The BadELF results table can be accessed as a pandas dataframe with the following code:

``` python
from simmate.database import connect
from simmate.apps.badelf.models import BadElf

badelf_results = BadElf.objects.all()
badelf_df = badelf_results.to_dataframe()
```

Explanations for each of the columns in the results can be viewed by calling

``` python
BadElf.get_column_docs()
```
which will return a dict object with column names as keys and doc information as values.

### (2) Local Files

If you are only interested in a small number of BadELF calculations, it may be more convenient to use the results written to local files. These can be found in a badelf_summary.csv file or the simmate_summary.yaml files. Additionally, a cif file will be written containing the labeled structure with "dummy" atoms representing electride electrons and other non-atomic features (See [ElectrideFinder](../finder/electride_finder.md) page for more info).

--------------------------------------------------------------------------------

## Use in python: the BadElfToolkit class

In addition to workflows, the BadELF app also contains a suite of python modules to aid in BadELF analysis. These can be accessed under the `simmate.apps.badelf.core` module. The most important of these is the BadElfToolkit class which allows users to run BadELF directly. Running BadELF in this way can give access to additional useful information, but is less user friendly. For more information, visit the [BadElfToolkit page](../toolkit/bad_elf_toolkit.md)


