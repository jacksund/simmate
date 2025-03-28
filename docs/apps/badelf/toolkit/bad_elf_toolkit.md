
# The BadElfToolkit and SpinBadElfToolkit Classes

--------------------------------------------------------------------------------

## About

The `BadElfToolkit` is the backbone for BadELF analyses. It automates the process of finding electride sites, running Bader partitioning through pybader, calculating the location of partitioning planes for atoms, and integrating charge. After the BadELF analysis is complete, all of the information collected through the process can be accessed directly from the `BadElfToolkit` class.

--------------------------------------------------------------------------------

## Basic Usage

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
from simmate.apps.badelf.core import SpinBadElfToolkit
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

For a complete list of parameters and their usage, see the [parameters page](../parameters.md)

### (2) Running BadELF and viewing results

Once the BadElfToolkit class is initialized, the BadELF algorithm is run as follows:

``` python
badelf_results = badelf.results
```

This will return a dictionary object that includes useful information such as the oxidation states and volumes of each atom/electride electron. The keys of this dictionary match with the columns for the BadElf table in the Simmate database. For complete explanations for each key, run `BadElf.get_column_docs()` as described in the [quick start](../quick_start.md) section. The regions assigned to a given atom or species can also be written to a CHGCAR or ELFCAR type file for convenient visualization in programs such as VESTA or OVITO:

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

In addition to the results stored in the dictionary, many of the results calculated through the BadELF process are stored as class properties. For example, a pandas dataframe representing the partitioning planes separating atoms can be obtained from `badelf.partitioning`. We encourage users to explore these properties if they are interested in the underlying components of the algorithm.
--------------------------------------------------------------------------------

## Accounting for Spin

The original formulation of BadELF assumed a closed system with identical spin-up and spin-down ELF. However, this assumption breaks down for many electrides (e.g. ferromagnetic Y2C). The original `BadElfToolkit` is designed to only use the first ELF or Charge Density grid provided to it, limiting it to calculations without spin polarization. To account for this, we have added the `SpinBadElfToolkit` class. This functions as a wrapper for the `BadElfToolkit` class, running the algorithm separately for the spin-up and spin-down ELF and charge density, then combining the results. The basic usage is essentially identical. To instantiate and run the algorithm through this class use the following code:

``` python
from simmate.apps.badelf.core import SpinBadElfToolkit

badelf = SpinBadElfToolkit.from_files(
    directory="/path/to/folder", # This is the directory where the files are located as well as the directory where BadELF will run
    partitioning_file="partitioning_filename", # e.g. ELFCAR
    charge_file="charge_filename", # e.g. CHGCAR
badelf_results = badelf.results
)
```

This will return a summary dict of the results. The keys in this dict will vary depending on differences in the spin-up and spin-down systems. If the spin-up and spin-down ELF is identical, or a non-spin-polarized ELF/charge density is provided, a standard BadElfTookit result will be returned with only one set of charges, site volumes, etc. for the entire system. In cases where the ELF differs, but all of the non-atomic features (electride electrons, covalent bonds, metallic bonds, etc.) are localized to the same site, the summary will include results for both the spin-up and spin-down systems as well as the combined results where possible. However, if the non-atomic features are not localized to the same site (e.g. ferromagnetic Y2C), only atomic results will be combined and all results related to non-atomic features will be reported separately for the spin-up and spin-down cases.

For more in-depth results, the individual `BadElftoolkit` classes for the spin-up and spin-down cases can be obtained by running:

``` python
badelf_spin_up = badelf.badelf_spin_up
badelf_spin_down = badelf.badelf_spin_down
```

!!! note
    We highly recommend performing spin polarized calculation and using the SpinBadElfToolkit. Electrides often exhibit differences in the spin-up and spin-down ELF. Even in cases where the differences are not extreme, the resulting charge should be calculated separately.

## Covalent and Metallic Systems

The original BadELF algorithm only provided results for strongly ionic systems. This is because the method for separating atoms relies on partitioning planes located at minima along the bonds between atoms and their neighbors. However, covalent and metallic bonds tend to appear as maxima in the ELF, resulting in no obvious minimum for placing the partitioning plane. To account for this, we have updated the method to treat covalent/metallic bonds similarly to electride electrons, partitioning them with a zero-flux surface. The results provide charges for these "shared features" as well as the atoms that neighbor them.

!!! warning
    Because these features result in there being no separating minima along bonds in the ELF, the planes separating atoms are instead located at the maxima. The original reasoning for the use of planes at minima was to reduce bias from large differences in ELF maxima and was supported by the similarity in location between the plane position and shannon ionic radii. Thus this placement of planes is not backed by rigorous testing, and it may be that a traditional 'zero-flux' partitioning works better. This can be set with the `algorithm` parameter. Do your own testing!

!!! note
    Currently, the charges associated with covalent/metallic features are not assigned to neighboring atoms in any way. There are many ways one may choose to do this based on electronegativity, atom distance, etc. This means that the calculated oxidation states will not be meaningful, and further analysis is needed on the part of the user. We are working to allow options for assigning these charges. It should be noted that this will have no effect on the charge calculated for electride sites.