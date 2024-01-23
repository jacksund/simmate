# The Warren Lab Application

!!! note
    The current maintainer of this application is [Sam Weaver](https://github.com/SWeav02)

--------------------------------------------------------------------------------

## About

The Warren Lab App is a product of Scott Warren's Materials Discovery Lab at the University of North Carolina (Chapel Hill). Our lab focuses on electrides, fluoride-ion batteries, and 2D materials. 

The `Warren Lab` application incorporates workflows for our lab's preferred DFT settings and common analyses. Registering this app will introduce numerous new workflow presets that build on several other apps (VASP, Bader, BadELF, etc.).

--------------------------------------------------------------------------------

## Installation

1. Add `warren_lab` (and it's dependencies) to the list of installed Simmate apps with:
``` bash
simmate-warren install
```

2. For Bader & BadELF workflows, make sure you have the Bader command (from the Henkleman group) installed using one of two options:
      - (*for beginners*) Install [Docker-Desktop](https://www.docker.com/products/docker-desktop/). Then run the following command:
          ``` bash
          simmate-bader setup docker
          ```
      - (*for experts*) Install Bader using [offical guides](http://theory.cm.utexas.edu/henkelman/code/bader/) and make sure `bader` is in the path

3. For VASP workflows, make sure you have the `vasp_std` command installed using one of two options:
      - (*for beginners*) Install [Docker-Desktop](https://www.docker.com/products/docker-desktop/). Then run the following command:
          ``` bash
          simmate-vasp setup docker --image example.com:vasp/latest
          ```

        !!! danger
            VASP is a commercial software, so we cannot provide Docker images for it. This is why you must provide a private image via `--image example.com:vasp/latest`.

      - (*for experts*) Install VASP using [offical guides](https://www.vasp.at/) and make sure `vasp_std` is in the path

4. Update your database to include custom tables from the `badelf` app:
``` shell
simmate database update
```

5. Ensure everything is configured correctly:
``` shell
simmate-warren test
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

## Helpful Resources

 - [Scott Warren](https://chem.unc.edu/faculty/warren-scott/) (UNC contact page)
 - [Lab Website](https://materials-lab.io/)

--------------------------------------------------------------------------------
