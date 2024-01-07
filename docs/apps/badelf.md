# BadELF Application

!!! note
    The current application maintainer is [Sam Weaver](https://github.com/SWeav02)

    The BadELF algorithm and application are based on the following research:
    
    - ["Counting Electrons in Electrides"](https://pubs.acs.org/doi/abs/10.1021/jacs.3c10876) (JACS 2023)

--------------------------------------------------------------------------------

## Overview of BadELF

BadELF is a method that combines Bader Charge Analysis and the Electron Localization Function (ELF) to predict oxidation states and perform population analysis of electrides. It uses Bader segmentation of the ELF to detect electride electrons and Voronoi segmentation of the ELF to identify atoms.

--------------------------------------------------------------------------------

## Application Features

The BadELF application provides workflows and utilities to streamline BadELF analysis.

--------------------------------------------------------------------------------

## Installation Steps

1. Ensure Simmate is installed and your database is reset.

2. Register the warrenapp with simmate by adding `- warrenapp.apps.WarrenConfig` to `~/simmate/my_env-apps.yaml`

3. Update your database to include custom tables from the warrenapp
``` shell
simmate database update
```

--------------------------------------------------------------------------------

## Basic Use

BadELF requires outputs from VASP calculations (like CHGCAR, ELFCAR, etc.). You can either generate these independently or use a simmate workflow to do it for you. 

### (a) From VASP Outputs

To use BadELF with VASP results, ensure your VASP settings generate a CHGCAR and ELFCAR with matching grid sizes. 

Create a yaml file:
``` yaml
# inside input.yaml
workflow_name: bad-elf-analysis.bad-elf.bad-elf

# all parameters below are optional
directory: /path/to/folder
cores: 4
find_electrides: true
min_elf: 0.5
algorithm: badelf
elf_connection_cutoff: 0
check_for_covalency: true
```

Then, execute the workflow:
``` bash
simmate workflows run input.yaml
```

### (b) From Input Structure

If you want Simmate to handle the VASP calculation, workflows are available that will first perform the required DFT and then BadELF. 

These workflows are stored in the `Warren Lab` app, which contains our lab's preferred VASP settings. Refer to the `Warren Lab` app for more details and to view the available workflows.

--------------------------------------------------------------------------------