
# The Warren Lab App

!!! note
    This app is currently maintained by [Sam Weaver](https://github.com/SWeav02)

--------------------------------------------------------------------------------

## About

Scott Warren's Materials Discovery Lab at the University of North Carolina (Chapel Hill) lab specicializes in electrides, fluoride-ion batteries, and 2D materials. 

This `Warren Lab` app contains workflows for our lab's preferred DFT settings and common analyses. By registering this app, you will add many new workflow presets that build on top of several other apps (VASP, Bader, BadELF, etc.).

--------------------------------------------------------------------------------

## Helpful links

 - [Scott Warren](https://chem.unc.edu/faculty/warren-scott/) (UNC contact page)
 - [lab website](https://materials-lab.io/)

--------------------------------------------------------------------------------

## Installation

1. Make sure you have Simmate installed and a working database.

2. Add the following apps to `~/simmate/my_env-apps.yaml`:
``` yaml
# Add app dependencies.
# NOTE!!! some of these are already present by default. Do not add duplicates
- simmate.apps.configs.VaspConfig
- simmate.apps.configs.BaderConfig
- simmate.apps.configs.BadelfConfig
# Add warren lab app.
- simmate.workflows.configs.WarrenLabConfig
```

3. Update your database to include custom tables:
``` bash
simmate database update
```

--------------------------------------------------------------------------------

## Workflows provided

### VASP (relaxation)

```
relaxation.vasp.warren-lab-hse
relaxation.vasp.warren-lab-hse-with-wavecar
relaxation.vasp.warren-lab-hsesol
relaxation.vasp.warren-lab-pbe
relaxation.vasp.warren-lab-pbe-metal
relaxation.vasp.warren-lab-pbe-with-wavecar
relaxation.vasp.warren-lab-pbesol
relaxation.vasp.warren-lab-scan
```

### VASP (static energy)

```
static-energy.vasp.warren-lab-hse
static-energy.vasp.warren-lab-hsesol
static-energy.vasp.warren-lab-pbe
static-energy.vasp.warren-lab-pbe-metal
static-energy.vasp.warren-lab-pbesol
static-energy.vasp.warren-lab-prebadelf-hse
static-energy.vasp.warren-lab-prebadelf-pbesol
static-energy.vasp.warren-lab-scan
```

### BadELF

```
bad-elf-analysis.badelf.badelf-pbesol
```

--------------------------------------------------------------------------------
