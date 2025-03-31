
# The ElectrideFinder Class

## About

The first step of the BadELF algorithm is to determine whether there are bare electrons in the system and, if so, where they are located. In the original paper this was done by using relatively simple distance and ELF value cutoffs. Since then, the `ElectrideFinder` method has evolved to be more rigorous. Using exclusively the ELF, charge density, and crystal structure, the `ElectrideFinder` class now automatically detects not only bare electrons, but atom cores, atom shells, covalent bonds, metallic features, and lone-pairs.

While it was originally conceived to support the BadELF algorithm, the current ElectrideFinder class can be used as a general tool for analyzing the ELF, providing considerably more information on each ELF feature than the BadElfToolkit class.

## Initializing the Class

The `ElectrideFinder` class can be initialized from files by running:

``` python
from simmate.apps.badelf.core import ElectrideFinder

finder = ElectrideFinder.from_files(
    directory="/path/to/folder", # This is the directory where the files are located
    # The parameters below are optional
    partitioning_file="partitioning_filename", # default ELFCAR
    charge_file="charge_filename", # default CHGCAR
    allow_spin = True, # treats spin-up and spin-down separately
    ignore_low_pseudopotentials = False, # ignores issues with missing core electrons
)
```

Alternatively, the `ElectrideFinder` class can be initialized by providing the ELF and charge density grids as Grid class objects. The Grid class inherits from pymatgen's VolumetricData class, and in principle allows for the use of codes other than VASP.

``` python
from simmate.apps.badelf.core import ElectrideFinder
from simmate.apps.bader.toolkit import Grid
from pathlib import Path

directory = Path("path/to/folder") # indicates the path to the folder where BadELF should run
partitioning_grid = Grid.from_file("path/to/partitioning_file")
charge_grid = Grid.from_file("path/to/partitioning_file")

finder = ElectrideFinder(
    directory=directory,
    partitioning_grid=partitioning_grid,
    charge_grid=charge_grid,
    # The parameters below are optional
    allow_spin = True, # treats spin-up and spin-down separately
    ignore_low_pseudopotentials = False, # ignores issues with missing core electrons        
)
```

## Constructing Bifurcation Graphs

Once the class is initialized, bifurcation graphs can be generated:

=== "spin polarized"
    ``` python
    graph_up, graph_down = finder.get_bifurcation_graphs(
        resolution = 0.02,
        shell_depth = 0.05,
        metal_depth_cutoff = 0.1,
        min_covalent_angle = 150,
        min_covalent_bond_ratio = 0.35,
        )
    ```

=== "not polarized"
    ``` python
    graph = finder.get_bifurcation_graphs(
        resolution = 0.02,
        shell_depth = 0.05,
        metal_depth_cutoff = 0.1,
        min_covalent_angle = 150,
        min_covalent_bond_ratio = 0.35,
        )
    ```

See our [parameters](../parameters) page for a complete description of each parameter. This returns [networkx](https://networkx.org/) graphs which can then be used to create a plotly plot:

``` python
plot = finder.get_bifurcation_plot(
        graph = graph,
        write_plot = True,
        plot_name = "my_bifurcation_plot"
        )
```

In the example above, the plot will be written to a .html file which can be directly viewed in your browser. Many python IDEs will also allow you to view the plot directly with

``` python
plot.show()
```

This should generate a plot similar to the following:

(insert bifurcation plot)

## Labeling Structures


