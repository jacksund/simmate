# The Warren Lab Application

!!! note
    The current maintainer of this application is [Sam Weaver](https://github.com/SWeav02)

--------------------------------------------------------------------------------

## Overview

The Warren Lab App is a product of Scott Warren's Materials Discovery Lab at the University of North Carolina (Chapel Hill). Our lab focuses on electrides, fluoride-ion batteries, and 2D materials. 

The `Warren Lab` application incorporates workflows for our lab's preferred DFT settings and common analyses. Registering this app will introduce numerous new workflow presets that enhance several other apps (VASP, Bader, BadELF, etc.).

--------------------------------------------------------------------------------

## Useful Resources

 - [Scott Warren](https://chem.unc.edu/faculty/warren-scott/) (UNC contact page)
 - [Lab Website](https://materials-lab.io/)

--------------------------------------------------------------------------------

## Installation

1. Ensure that Simmate is installed and that you have a functioning database.

2. Incorporate the following apps into `~/simmate/my_env-apps.yaml`:
``` yaml
# Include app dependencies.
# IMPORTANT: Some of these may already be present by default. Avoid adding duplicates
- simmate.apps.configs.VaspConfig
- simmate.apps.configs.BaderConfig
- simmate.apps.configs.BadelfConfig
# Include the Warren Lab app.
- simmate.workflows.configs.WarrenLabConfig
```

3. Update your database to incorporate custom tables:
``` bash
simmate database update
```

--------------------------------------------------------------------------------

## Included Workflows

### VASP (Relaxation)

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

### VASP (Static Energy)

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