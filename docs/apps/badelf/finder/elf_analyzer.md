
# The ElfAnalyzerToolkit Class

## About

The first step of the BadELF algorithm is to determine whether there are bare electrons in the system and, if so, where they are located. In the original paper this was done by using relatively simple distance and ELF value cutoffs. Since then, the `ElfAnalyzerToolkit` method has evolved to be more rigorous. Using exclusively the ELF, charge density, and crystal structure, the `ElfAnalyzerToolkit` class now automatically detects not only bare electrons, but atom cores, atom shells, covalent bonds, metallic features, and lone-pairs.

While it was originally conceived to support the BadELF algorithm, the current ElfAnalyzerToolkit class can be used as a general tool for analyzing the ELF, providing considerably more information on each ELF feature than the BadElfToolkit class.

Explanations for each parameter can be found as a subsection of the `elf_analyzer_kwargs` section on our [parameters page](/parameters.md)

## Initializing the Class

The `ElfAnalyzerToolkit` class can be initialized from files or by providing the ELF and charge density grids as Grid class objects. The Grid class inherits from pymatgen's VolumetricData class, and in principle allows for the use of codes other than VASP.


=== "from file"
    ``` python
    from simmate.apps.badelf.core import ElfAnalyzerToolkit
    
    finder = ElfAnalyzerToolkit.from_files(
        directory="/path/to/folder", # This is the directory where the files are located
        # The parameters below are optional
        elf_file="partitioning_filename", # default ELFCAR
        charge_file="charge_filename", # default CHGCAR
        separate_spin = True, # Treats spin-up and spin-down separately
        ignore_low_pseudopotentials = False, # ignores issues with missing core electrons
        downscale_resolution: int = 1200, # Downscales the ELF and charge density unless set to None
    )
    ```

=== "from grid class"
    ``` python
    from simmate.apps.badelf.core import ElfAnalyzerToolkit
    from simmate.apps.bader.toolkit import Grid
    from pathlib import Path
    
    directory = Path("path/to/folder") # indicates the path to the folder where BadELF should run
    elf_grid = Grid.from_file("path/to/partitioning_file")
    charge_grid = Grid.from_file("path/to/partitioning_file")
    
    finder = ElfAnalyzerToolkit(
        directory=directory,
        elf_grid=partitioning_grid,
        charge_grid=charge_grid,
        # The parameters below are optional
        separate_spin = True, # treats spin-up and spin-down separately
        ignore_low_pseudopotentials = False, # ignores issues with missing core electrons        
        downscale_resolution: int = 1200, # Downscales the ELF and charge density unless set to None
    )
    ```

## Getting Results

Once the class is initialized, all of the results can be obtained:

``` python
results = finder.get_full_analysis(
    resolution=0.01,
    include_lone_pairs=False,
    metal_depth_cutoff=0.1,
    min_covalent_angle=135,
    min_covalent_bond_ratio=0.4,
    shell_depth=0.05,
    electride_elf_min=0.5,
    electride_depth_min=0.2,
    electride_charge_min=0.5,
    electride_volume_min=10,
    electride_radius_min=0.3,
    radius_refine_method="linear",
    write_results=True,
)
```

This will return a dictionary with keys for a bifurcation graph, bifurcation plot, and a labeled structure. If the `separate_spin=True` tag was used, there will be two of each of these for the up and down cases. Descriptions for each of these are below.

## Bifurcation Graphs

The BifurcationGraph class is a custom network class built off of [networkx](https://networkx.org/). The graphs are constructed first during the process, and contain all of the most important information. Each node represents a unique topological domain at various ELF values. Reducible features are connected to their child irreducible features by the edges. The graphs can be obtain as follows:

=== "spin polarized"
    ``` python
    graph_up = results["graph_up"]
    graph_down = results["graph_down"]
    ```

=== "not polarized"
    ``` python
    graph = results["graph"]
    ```

## Bifurcation Plots

The bifurcation plots are [Plotly](https://plotly.com/graphing-libraries/) `graph_objects` constructed directly from the `BifurcationGraph`s above. They can be obtained as follows:

=== "spin polarized"
    ``` python
        plot_up = results["plot_up"]
        plot_down = results["plot_down"]
    ```

=== "not polarized"
    ``` python
        plot = results["plot"]
    ```

If `write_results=True`, the plots will be written to a .html file which can be directly viewed in your browser. Alternatively, many python IDEs will also allow you to view the plot directly with

``` python
plot.show()
```

This should generate a plot similar to those on the [background page](../background.md).

These plots are the easiest way to visualize the ELF features in your system. The Y-axis represents the ELF value at which each domain first separates from its parent domain. Hovering over each node in the graph will provide additional information about the domain it represents. For reducible domains, this includes information like the number of atoms it surrounds, and their structure index. For irreducible domains it includes things such as charge, volume, ELF maximum, depth, distance to nearest atom, and more. We recommend loading your ELF into a program such as VESTA or OVITO and different ELF values with the plot to help get used to what it represents. 

!!! note
    The charge provided by this method is identical to running the `BadElfToolkit` with the `zero-flux` algorithm. This matches a more traditional ELF topology analysis, rather than separating atoms with planes.

## Labeled Structures

The labeled structures are [pymatgen](https://pymatgen.org/) `Structure` objects with 'dummy' atoms representing different types of ELF features. This is primarily used by the `BadElfToolkit` for BadELF analysis, but is also useful for visualization.

To get the labeled structures:

=== "spin polarized"
    ``` python
        labeled_structure_up = results["structure_up"]
        labeled_structure_down = results["structure_down"]
    ```

=== "not polarized"
    ``` python
        labeled_structure = results["structure"]
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