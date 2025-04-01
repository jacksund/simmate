# BadELF in Python: The BadElfToolkit Class

In addition to running BadELF as a Simmate workflow, the BadELF app also contains a suite of python modules for assisting in BadELF analysis. These can be accessed under the `simmate.apps.badelf.core` module. The most useful of these are the `BadElfToolkit`/`SpinBadElfToolkit` classes which allow users to run BadELF directly and the [ElfAnalyzerToolkit](../finder/elf_analyzer) class which helps analyze features of the ELF. Directly using these classes can provide additional control over the process that is unavailable when using Simmate's workflow system.

The `BadElfToolkit` is the backbone for BadELF analyses, and is used under the hood when BadELF is called through .yaml files or the command line. It automates the process of finding electride sites, running Bader partitioning through pybader, calculating the location of partitioning planes for atoms, and integrating charge. After the BadELF analysis is complete, all of the information collected through the process can be accessed directly from the `BadElfToolkit` class. The `SpinBadElfToolkit` class is a wrapper for the `BadElfToolkit` class with the same basic usage. It creates two `BadElfToolkit` instances for the spin-up and spin-down ELF/charge density, and combines the results from the two. 

!!! note
    It is recommended to use the `SpinBadElfToolkit` by default, even if you are not providing results from a spin-polarized calculation. This is because the `SpinBadElfToolkit` class is designed to automatically detect if a calculation is not spin-polarized.

!!! warning
    Running BadELF directly through the `BadElfToolkit`/`SpinBadElfToolkit` will not save results to your Simmate database.

Using the `BadElfToolkit` class requires two basic steps:

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
from simmate.apps.badelf.core import BadElfToolkit
from simmate.apps.bader.toolkit import Grid
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

When initializing the BadELF class through either of these methods, the same optional parameters used in the .yaml file are also available. For a complete list of parameters and their usage, see the [parameters page](../parameters)

### (2) Running BadELF and viewing results

Once the BadElfToolkit class is initialized, the BadELF algorithm is run as follows:

``` python
badelf_results = badelf.results
```

This will return a dictionary object that includes useful information such as the oxidation states and volumes of each atom/electride electron. The keys of this dictionary match with the columns for the BadElf table in the Simmate database. 

In addition to the results dictionary, many other results calculated through the BadELF process are available through class properties/methods. These results may not be available when using Simmate's default workflow system. For example, regions assigned to a given atom or species can be written to a CHGCAR or ELFCAR type file for convenient visualization in programs such as VESTA or OVITO:

```python
# Write ELF or Charge Density for all atoms of a given type
badelf.write_species_file(
    file_type="ELFCAR", # can also be CHGCAR
    species="E", # E is used as a placeholder for electride electrons
)

# Write ELF or Charge Density for one atom
badelf.write_atom_file(
    file_type="ELFCAR", # can also be CHGCAR
    atom_index=0, # The index of the atom to write the charge for
)
```

Other results, such as a pandas dataframe representing the partitioning planes separating atoms, are stored as class properties (e.g. `badelf.partitioning`). We encourage users to explore these properties if they are interested in the underlying components of the algorithm.

--------------------------------------------------------------------------------

