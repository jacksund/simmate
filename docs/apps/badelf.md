
# The BadELF App

!!! note
    The current maintainer of this application is [Sam Weaver](https://github.com/SWeav02)

    The BadELF algorithm and application are based on the following research:
    
    - ["Counting Electrons in Electrides"](https://pubs.acs.org/doi/abs/10.1021/jacs.3c10876) (JACS 2023)

--------------------------------------------------------------------------------

## About

BadELF is a method that combines Bader Charge Analysis and the Electron Localization Function (ELF) to predict oxidation states and perform population analysis of electrides. It uses Bader segmentation of the ELF to detect electride electrons and Voronoi segmentation of the ELF to identify atoms.

Simmate's BadELF application provides workflows and utilities to streamline BadELF analysis. 

!!! note
    BadELF currently only works with VASP, but we are interested in expanding its use to other ab initio software. If you are interested in this, let us know, as that will help to make this a higher priority.

--------------------------------------------------------------------------------

## Installation

1. This app uses `mp-pyrho` and `pybader` under the hood. Install these with:
``` bash
conda install -n my_env -c conda-forge mp-pyrho pybader
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
find_electrides: true
electride_finder_cutoff: 0.5
algorithm: badelf
covalent_bond_alg: zero-flux
ignore_low_pseudopotentials: false
```

And run the workflow:
``` bash
simmate workflows run input.yaml
```

Alternatively, the BadELF algorithm can be run from the command line without a yaml file:
``` bash
simmate workflows run-quick bad-elf.badelf.badelf --directory /path/to/folder
```

### (b) from structure

If you would prefer to have Simmate handle the VASP calculation, workflows are available that will first run the required DFT and then BadELF. 

These workflows are stored in the `Warren Lab` app, which contains our lab's preferred VASP settings. Refer to the `Warren Lab` app for more details and to view the available workflows.

--------------------------------------------------------------------------------

## Use in python: the BadElfToolkit class

In addition to workflows, the BadELF app also contains a suite of python modules to aid in BadELF analysis. These can be accessed under the `simmate.apps.badelf.core` module. The most useful of these is the BadElfToolkit class which allows users to run BadELF directly. Running BadELF in this way involves two steps:

### (1) Initializing the BadElfToolkit class

The BadElfToolkit class can be initialized with the `from_files` method:
``` python
from simmate.apps.badelf.core import BadElfToolkit

badelf = BadElfToolkit.from_files(
    directory="/path/to/folder", # This is the directory where the files are located as well as the directory where BadELF will run
    partitioning_file="partitioning_filename", # e.g. ELFCAR
    charge_file="charge_filename", # e.g. CHGCAR
)
```

Alternatively, the BadElfToolkit can be initialized by providing the partitioning and charge density grids as Grid class objects. The Grid class inherits from pymatgen's VolumetricData class.

``` python
from simmate.apps.badelf.core import BadElfToolkit, Grid
from pathlib import Path

directory = Path("path/to/folder") # indicates the path to the folder where BadELF should run
partitioning_grid = Grid.from_file("path/to/partitioning_file")
charge_grid = Grid.from_file("path/to/partitioning_file")

badelf = BadElfToolkit(
    directory=directory,
    partitioning_grid=partitioning_grid,
    charge_grid=charge_grid        
)
```

### (2) Running BadELF and viewing results

Once the BadElfToolkit class is initialized, the BadELF algorithm is run as follows:

``` python
badelf_results = badelf.results
```

This will return a dictionary object that includes useful information such as the oxidation states and volumes of each atom/electride electron. The volumes assigned to a given atom or species can also be written to a CHGCAR or ELFCAR type file for convenient visualization in programs such as VESTA or OVITO:

```python
# Write ELF or Charge Density for all atoms of a given type
badelf.write_species_file(
    file_type="ELFCAR", # can also be CHGCAR
    species="X", # X is used as a placeholder for electride electrons
)

# Write ELF or Charge Density for one atom
badelf.write_atom_file(
    file_type="ELFCAR", # can also be CHGCAR
    atom_index=0, # The index of the atom to write the charge for
)
```

--------------------------------------------------------------------------------
