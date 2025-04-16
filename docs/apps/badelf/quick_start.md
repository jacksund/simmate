
# The BadELF App

!!! note
    The current maintainer of this application is [Sam Weaver](https://github.com/SWeav02)

    The BadELF algorithm and application are based on the following research:
    
    - ["Counting Electrons in Electrides"](https://pubs.acs.org/doi/abs/10.1021/jacs.3c10876) (JACS 2023)
    - ["Assessing Dimensionality in Electrides"](https://pubs.acs.org/doi/10.1021/acs.jpcc.4c06803) (JPCC 2025)
    
--------------------------------------------------------------------------------

## About

BadELF is a method that combines Bader Charge Analysis and the Electron Localization Function (ELF) to predict oxidation states and perform population analysis of electrides. It uses Bader segmentation of the ELF to calculate the charge on electride electrons and Voronoi segmentation of the ELF to calculate charge on atoms. Since the original BadELF paper was published, additional functionality has been added to handle systems with covalent/metallic features and for handling the up/down spin ELF and charge density separately.

An additional tool, the [ElfAnalyzerToolkit](finder/elf_analyzer.md) has also been developed to assist in analyzing features in the ELF. This tool is designed for in-depth ELF topological analysis, and can also perform a simple charge analysis using traditional zero-flux surfaces.

!!! note
    BadELF currently only works with VASP, but we are interested in expanding its use to other ab initio software. If you are interested in this, let us know, as that will help to make this a higher priority.

--------------------------------------------------------------------------------

## Installation

Follow the instructions for [installing simmate](/getting_started/installation/quick_start.md). Then BadELF can be set up with the following instructions.

1. This app uses `pybader` and `networkx` under the hood. Install this with:
``` bash
conda install -n my_env -c conda-forge pybader networkx
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

BadELF requires outputs from VASP calculations (e.g. the CHGCAR, ELFCAR, etc.). You can either (1) generate these on your own or (2) run a simmate workflow that does it for you. 

### (1) from VASP outputs

The BadELF algorithm can be run in a folder with VASP results. Please ensure your VASP settings generate a CHGCAR and ELFCAR with matching grid sizes. 

Create a yaml file:
``` yaml
# inside input.yaml
workflow_name: bad-elf.badelf.badelf
directory: /path/to/folder

# all parameters below are optional
find_electrides: true # Whether or not to use ElfAnalyzerToolkit to automatically find electrides
labeled_structure_up: none # If find_electrides is false, a labeled structure with dummy atoms (see ElfAnalyzerToolkit docs)
labeled_structure_down: none # Same as above, but for spin down system
elf_analyzer_kwargs: # Settings for the ElfAnalyzerToolkit. See ElfAnalyzerToolkit docs for more info
    resolution: 0.01,
    include_lone_pairs: false,
    include_shared_features: true,
    metal_depth_cutoff: 0.1,
    min_covalent_angle: 135,
    min_covalent_bond_ratio: 0.35,
    shell_depth: 0.05,
    electride_elf_min: 0.5,
    electride_depth_min: 0.2,
    electride_charge_min: 0.5,
    electride_volume_min: 10,
    electride_radius_min: 0.3,
    radius_refine_method: linear,
    write_results: true,
algorithm: badelf # The algorithm for separating atoms and electride sites
separate_spin: true # Whether to treat spin-up and spin-down systems separately
shared_feature_algorithm: zero-flux # The algorithm for separating covalent/metallic features
shared_feature_separation_method: pauling # The method used to assigne covalent/metallic charge to atoms
ignore_low_pseudopotentials: false # Forces algorithm to ignore errors related to PPs with few electrons
downscale_resolution: 1200 # The resolution in voxels/A^3 to downscale grids to in ElfAnalysisToolkit
write_electride_files: false # Writes the bare electron volume ELF and charge
write_ion_radii: true # Writes the ionic radius calculated from the ELF for each atom
write_labeled_structure: true # Writes a cif file with dummy atoms for each non-atomic ELF feature
```

And run the workflow:
``` bash
simmate workflows run input.yaml
```

Alternatively, the BadELF workflow can be run from the command line without a yaml file:
``` bash
simmate workflows run-quick bad-elf.badelf.badelf --directory /path/to/folder
```

If you plan to run many BadELF calculations or need to manipulate the results in post, it may be more convenient to run the workflow using python. See the [full guides](/full_guides/workflows/basic_use.md) for more details. For a complete list of parameters and their usage, see our [parameters page](/parameters.md)

### (2) from structure

If you would prefer to have Simmate handle the VASP calculation, workflows are available that will first run the required DFT and then BadELF. 

These workflows are stored in the `Warren Lab` app, which contains our lab's preferred VASP settings. Refer to the [`Warren Lab` app](/apps/warren_lab.md) for more details and to view the available workflows.

--------------------------------------------------------------------------------

## Viewing Results

Running BadELF as described above uses Simmate's Workflow system. The results of these workflows can be viewed in a couple of ways.

### (1) The Database

When setting up simmate, you created a local or cloud database. Results from any workflow run through simmate will be stored here, allowing for the automation of high-throughput calculations. Basic usage of the database can be found in our [getting started docs](/getting_started/database/quick_start.md). The BadELF results table can be accessed through python as a pandas dataframe:

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

If you are only interested in a small number of BadELF calculations, it may be more convenient to use the results written to local files. These can be found in the `badelf_summary.csv` file or the `simmate_summary.yaml` files. Additionally, a cif file will be written containing the labeled structure with "dummy" atoms representing electride electrons and other non-atomic features (See [ElfAnalyzerToolkit](finder/elf_analyzer.md) page for more info).

--------------------------------------------------------------------------------

## Covalent and Metallic Systems

Covalent and metallic features in the ELF conflict with the original BadELF algorithm (see [Background](background.md)). The current version of BadELF offers several ways to handle these features:

### (1) Split Them with Planes

Similar to placing planes at minima in the ELF in ionic systems, one can place planes at maxima in covalent/metallic systems. This results in the features being divided and their charge assigned to nearby atoms. To handle covalent/metallic bonds this way use the follow `shared_feature_separation_method`:

``` yaml
shared_feature_separation_method: plane
```

!!! warning
    Metallic features are not always along bonds. If this is the case, this method may not split them effectively. Additionally, no information will be returned about each shared feature.

### (2) Treat them Separately

Alternatively, one can treat covalent and metallic bonds as their own entities, similar to the treatment of bare electrons in electrides. In these cases, one needs to decide how to separate these features from the nearby atoms. The options available are with a zero-flux surface or a voronoi like plane and can be set with the `shared_feature_algorithm` parameter. Additionally, one must decide how to assign the charge from these 'shared features' to the nearby atoms. We currently offer two methods for doing this: splitting them equally, and splitting by pauling electronegativity. Splitting equally divides the features equally to each neighboring atom. Splitting by pauling EN gives more charge to more electronegative atoms.

=== "equal split"
    ``` yaml
    shared_feature_algorithm: zero-flux # or voronoi
    shared_feature_separation_method: equal
    ```
    
=== "pauling electronegativity"
    ``` yaml
    shared_feature_algorithm: zero-flux # or voronoi
    shared_feature_separation_method: pauling
    ```

!!! note
    In systems where atoms are always surrounded by covalent/metallic bonds, there will be very little difference in results between using planes ore zero-flux surfaces to separate atoms from one another. However, the zero-flux surface separation is much faster. If you are confident your system is heavily metallic or covalent, we suggest setting `algorithm: zero-flux`. In systems where this is not the case, this will just result in atom oxidation states tending more towards integer values.
--------------------------------------------------------------------------------

## Accounting for Spin

Electrides often have differing ELF and charge density for the spin-up and spin-down systems from spin-polarized calculations. Therefore, BadELF by default treats the spin-up and spin-down systems separately and combines the results where possible in post. This differs from the original algorithm which assumed a closed system where the spin-up and spin-down systems match. If a closed-system treatment is preferred set:

``` yaml
separate_spin: false
```


