
# The BadELF App

!!! note
    This app is currently maintained by [Sam Weaver](https://github.com/SWeav02)

    Further, this app and its BadELF algorithm is based on the following study:
    
    - ["Counting Electrons in Electrides"](https://pubs.acs.org/doi/abs/10.1021/jacs.3c10876) (JACS 2023)

--------------------------------------------------------------------------------

## About BadELF

Bader Charge Analysis (or "Bader" for short) is a process of partitioning charge density in order to predict oxidation states. Then the Electron Localization Function (ELF) is a popular scheme for visualizing chemically important features in molecules and solids.

BadELF builds on top of these two ideas. The algorithm uses Bader segmentation of the ELF to find the electride electrons (if any) and Voronoi segmentation of the ELF to identify atoms. Thus BadELF is intended as an alternative method to run population analysis / predict oxidation states of electrides.

--------------------------------------------------------------------------------

## About this app

This app provides workflows and utilities to help with BadELF analysis.

--------------------------------------------------------------------------------

## Installation

1. Make sure you have Simmate installed and have reset your database.

2. Register the warrenapp with simmate by adding `- warrenapp.apps.WarrenConfig` to `~/simmate/my_env-apps.yaml`

3. Update your database to include custom tables from the warrenapp
``` shell
simmate database update
```

--------------------------------------------------------------------------------

## Basic Use

BadELF requires the outputs from VASP calculations (e.g. the CHGCAR, ELFCAR, etc.). You can either (a) generate these on your own or (b) run a simmate workflow that does it for you. 

### (a) from VASP outputs

The BadELF algorithm can be run in a folder with VASP results. Please note that your VASP settings must produce a CHGCAR and ELFCAR with the same grid size.
``` bash
simmate-badelf run
```

### (b) from structure

If you would prefer to have Simmate handle the VASP calculation, there are workflows that will first run the required DFT and then BadELF. 

These workflows are stored in the `Warren Lab` app because we are our lab's preferred VASP settings there. View the `Warren Lab` app for more information and to see the workflows available.

--------------------------------------------------------------------------------
