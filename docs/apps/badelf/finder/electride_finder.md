
# The ElectrideFinder Class

## About

The first step of the BadELF algorithm is to determine whether there are bare electrons in the system and, if so, where they are located. In the original paper this was done by using relatively simple distance and ELF value cutoffs. Since then, the `ElectrideFinder` method has evolved to be more rigorous. Using exclusively the ELF, charge density, and crystal structure, the `ElectrideFinder` class now automatically detects not only bare electrons, but atom cores, atom shells, covalent bonds, metallic features, and lone-pairs.

While it was originally conceived to support the BadELF algorithm, the current ElectrideFinder class can be used as a general tool for analyzing the ELF, providing considerably more information on each ELF feature than the BadElfToolkit class.

Explanations for each parameter can be found as a subsection of the `electride_finder_kwargs` section on our [parameters page](../../../../parameters)

## Initializing the Class

The `ElectrideFinder` class can be initialized from files by running:

``` python
from simmate.apps.badelf.core import ElectrideFinder

finder = ElectrideFinder.from_files(
    directory="/path/to/folder", # This is the directory where the files are located
    # The parameters below are optional
    elf_file="partitioning_filename", # default ELFCAR
    charge_file="charge_filename", # default CHGCAR
    separate_spin = True, # Treats spin-up and spin-down separately
    ignore_low_pseudopotentials = False, # ignores issues with missing core electrons
)
```

Alternatively, the `ElectrideFinder` class can be initialized by providing the ELF and charge density grids as Grid class objects. The Grid class inherits from pymatgen's VolumetricData class, and in principle allows for the use of codes other than VASP.

``` python
from simmate.apps.badelf.core import ElectrideFinder
from simmate.apps.bader.toolkit import Grid
from pathlib import Path

directory = Path("path/to/folder") # indicates the path to the folder where BadELF should run
elf_grid = Grid.from_file("path/to/partitioning_file")
charge_grid = Grid.from_file("path/to/partitioning_file")

finder = ElectrideFinder(
    directory=directory,
    elf_grid=partitioning_grid,
    charge_grid=charge_grid,
    # The parameters below are optional
    separate_spin = True, # treats spin-up and spin-down separately
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

This returns custom BifurcationGraphs which are built out from [networkx](https://networkx.org/). Plots can then be generated from each graph:

``` python
plot = finder.get_bifurcation_plot(
            graph = graph,
            write_plot = True,
            plot_name = "my_bifurcation_plot.html"
        )
```

Alternatively, there is a method for generating both plots without the graph object if you are only interested in visualization:

=== "spin polarized"
    ``` python
        plot_up, plot_down = finder.get_bifurcation_plots(
                    write_plot = True,
                    plot_name = "my_bifurcation_plot.html",
                    resolution = 0.02,
                    shell_depth = 0.05,
                    metal_depth_cutoff = 0.1,
                    min_covalent_angle = 150,
                    min_covalent_bond_ratio = 0.35,
                )
    ```

=== "not polarized"
    ``` python
        plot = finder.get_bifurcation_plots(
                    write_plot = True,
                    plot_name = "my_bifurcation_plot.html",
                    resolution = 0.02,
                    shell_depth = 0.05,
                    metal_depth_cutoff = 0.1,
                    min_covalent_angle = 150,
                    min_covalent_bond_ratio = 0.35,
                )
    ```

In the examples above, the plot will be written to a .html file which can be directly viewed in your browser. Alternatively, many python IDEs will also allow you to view the plot directly with

``` python
plot.show()
```

This should generate a plot similar to those on the [background page](../background).

The Y-axis represents the ELF value at which each domain first separates from its parent domain. Hovering over each node in the graph will provide additional information about the domain it represents. For reducible domains, this includes information like the number of atoms it surrounds, and their structure index. For irreducible domains it includes things such as charge, volume, ELF maximum, depth, distance to nearest atom, and more. We recommend loading your ELF into a program such as VESTA or OVITO and different ELF values with the plot to help get used to what it represents. 

!!! note
    The charge provided by this method is identical to running the `BadElfToolkit` with the `zero-flux` algorithm. This matches a more traditional ELF topology analysis, rather than separating atoms with planes.

## Labeling Structures

In addition to creating bifurcation plots, the `ElectrideFinder` can also be used to generate pymatgen Structure objects with "dummy" atoms representing different types of domains. This is primarily used by the `BadElfToolkit` for BadELF analysis, but is also useful for visualization.

To generate a labeled structures:

=== "spin polarized"
    ``` python
        labeled_structure_up, labeled_structure_down = finder.get_labeled_structures(
                    include_lone_pairs = false,
                    include_shared_features = false,
                    resolution = 0.02,
                    shell_depth = 0.05,
                    metal_depth_cutoff = 0.1,
                    min_covalent_angle = 150,
                    min_covalent_bond_ratio = 0.35,
                    # Cutoffs for Electrides
                    electride_elf_min = 0.5,
                    electride_depth_min = 0.2,
                    electride_charge_min = 0.5,
                    electride_volume_min = 10,
                    electride_radius_min = 0.3,
                )
    ```

=== "not polarized"
    ``` python
        labeled_structure = finder.get_labeled_structure(
                    include_lone_pairs = false,
                    include_shared_features = false,
                    resolution = 0.02,
                    shell_depth = 0.05,
                    metal_depth_cutoff = 0.1,
                    min_covalent_angle = 150,
                    min_covalent_bond_ratio = 0.35,
                    # Cutoffs for Electrides
                    electride_elf_min = 0.5,
                    electride_depth_min = 0.2,
                    electride_charge_min = 0.5,
                    electride_volume_min = 10,
                    electride_radius_min = 0.3,
                )
    ```

If the structure has any non-atomic features, they will be labeled with Dummy atoms. The following labels are used:

| Feature | Label | 
| --------- | --------- | 
| Covalent Bond      | "Z"      | 
| Lone-Pair   | "Lp"     | 
| Metal     | "M"      | 
| Electride     | "E"     | 
| Other Bare Electron       | "Le"       | 

!!! note
    Admittedly, some of these labels are not intuitive. This is due to pymatgen's Structure object limiting dummy atom labels to symbols that don't start with letters shared by an element (e.g. "Cov" isn't available because of C and Co)

The labeled structures can then be written to files for visualization in software such as VESTA or OVITO.

=== "spin polarized"
    ``` python
        labeled_structure_up.to("my_structure_up.cif", "cif")
        labeled_structure_down.to("my_structure_down.cif", "cif")
    ```

=== "not polarized"
    ``` python
        labeled_structure.to("my_structure.cif", "cif")
    ```