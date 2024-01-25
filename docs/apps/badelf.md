
# The BadELF App

!!! note
    The current maintainer of this application is [Sam Weaver](https://github.com/SWeav02)

    The BadELF algorithm and application are based on the following research:
    
    - ["Counting Electrons in Electrides"](https://pubs.acs.org/doi/abs/10.1021/jacs.3c10876) (JACS 2023)

--------------------------------------------------------------------------------

## About

BadELF is a method that combines Bader Charge Analysis and the Electron Localization Function (ELF) to predict oxidation states and perform population analysis of electrides. It uses Bader segmentation of the ELF to detect electride electrons and Voronoi segmentation of the ELF to identify atoms.

Simmate's BadELF application provides workflows and utilities to streamline BadELF analysis.

--------------------------------------------------------------------------------

## Installation

1. Add `badelf` (and it's dependencies) to the list of installed Simmate apps with:
``` bash
simmate config add badelf
```

2. Make sure you have the Bader command (from the Henkleman group) installed using one of two options:
      - (*for beginners*) Install [Docker-Desktop](https://www.docker.com/products/docker-desktop/). Then run the following command:
          ``` bash
          simmate config update "bader.docker.enable=True"
          ```
      - (*for experts*) Install Bader using [offical guides](http://theory.cm.utexas.edu/henkelman/code/bader/) and make sure `bader` is in the path

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
cores: 4
find_electrides: true
min_elf: 0.5
algorithm: badelf
elf_connection_cutoff: 0
check_for_covalency: true
```

And run the workflow:
``` bash
simmate workflows run input.yaml
```

### (b) from structure

If you would prefer to have Simmate handle the VASP calculation, workflows are available that will first run the required DFT and then BadELF. 

These workflows are stored in the `Warren Lab` app, which contains our lab's preferred VASP settings. Refer to the `Warren Lab` app for more details and to view the available workflows.

--------------------------------------------------------------------------------
