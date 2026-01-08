# The BaderKit Application

!!! note
    The current maintainer of this application is [Sam Weaver](https://github.com/SWeav02)

--------------------------------------------------------------------------------

## About

Bader Charge Analysis ("Bader" for short) is a technique for partitioning charge density to predict oxidation states. This module is specifically tailored for the [BaderKit](https://github.com/SWeav02/baderkit) python package. BaderKit
is also the home repository for the [BadELF](https://pubs.acs.org/doi/10.1021/acs.jpcc.4c06803) method as well as several tools for analyzing the
electron localization function (ELF).

Simmate's Baderkit app builds workflows and utilities on top of the BaderKit code. Typically, other workflows oversee the execution of the workflows registered in this app. For example, workflows in the `Warren Lab` app combine VASP, BaderKit and rational settings. If you are here, you are most likely also interested in automating Bader or BadELF analysis, and should either use the presets in the `Warren Lab` app or build out your own workflows staging DFT into your desired analysis.

In addition to the parameters presented by simmates documentation, any parameter used in the underlying BaderKit classes can also be set by using extra keyword arguments in the `.run` method of any workflow in this app. For information on the available paramaters, see the [BaderKit Docs](https://sweav02.github.io/baderkit/)

--------------------------------------------------------------------------------

## Installation

1. Add `baderkit` to the list of installed Simmate apps with:
``` bash
simmate config add baderkit
```

2. Make sure you have the `baderkit` package installed in the same environment as Simmate. For help, see the the [BaderKit Docs](https://sweav02.github.io/baderkit/)

3. Update your database to include custom tables from the app:
``` shell
simmate database update
```

4. Ensure everything is configured correctly:
``` shell
simmate config test baderkit
```

--------------------------------------------------------------------------------

## Included Workflows

### Bader

```
bader.baderkit.bader
```

### BadELF

```
badelf.baderkit.badelf
badelf.baderkit.spin-badelf
```

### ElfLabeler

```
elf-analysis.baderkit.elf-analysis
elf-analysis.baderkit.spin-elf-analysis
```

--------------------------------------------------------------------------------

## Helpful Resources

 - [BaderKit Documentation](https://sweav02.github.io/baderkit/)
 - [Scott Warren](https://chem.unc.edu/faculty/warren-scott/) (UNC contact page)
 - [Lab Website](https://materials-lab.io/)

--------------------------------------------------------------------------------
