# The Warren Lab Application

!!! note
    The current maintainer of this application is [Sam Weaver](https://github.com/SWeav02)

--------------------------------------------------------------------------------

## About

The Warren Lab App is a product of Scott Warren's Materials Discovery Lab at the University of North Carolina (Chapel Hill). Our lab focuses on electrides, fluoride-ion batteries, and 2D materials. 

The `Warren Lab` application incorporates workflows for our lab's preferred DFT settings and common analyses. Registering this app will introduce numerous new workflow presets that build on several other apps (VASP, BaderKit, etc.).

--------------------------------------------------------------------------------

## Installation

1. Add `warren_lab` (and it's dependencies) to the list of installed Simmate apps with:
``` bash
simmate config add warren_lab
```

2. For Bader & BadELF workflows, make sure you have the Bader command (from the Henkleman group) installed using one of two options:
      - (*for beginners*) Install [Docker-Desktop](https://www.docker.com/products/docker-desktop/). Then run the following command:
          ``` bash
          simmate config update "bader.docker.enable=True"
          ```
      - (*for experts*) Install Bader using [offical guides](http://theory.cm.utexas.edu/henkelman/code/bader/) and make sure `bader` is in the path

3. For VASP workflows, make sure you have the `vasp_std` command installed using one of two options:
      - (*for beginners*) Install [Docker-Desktop](https://www.docker.com/products/docker-desktop/). Then run the following commands:
          ``` bash
          simmate config update "vasp.docker.enable=True"
          simmate config update "vasp.docker.image=example.com:vasp/latest"
          ```

        !!! danger
            VASP is a commercial software, so we cannot provide Docker images for it. This is why you must provide a private image via `image=example.com:vasp/latest`.

      - (*for experts*) Install VASP using [offical guides](https://www.vasp.at/) and make sure `vasp_std` is in the path

4. Update your database to include custom tables from the app:
``` shell
simmate database update
```

5. Ensure everything is configured correctly:
``` shell
simmate config test warren_lab
```

--------------------------------------------------------------------------------

## Included Workflows

### VASP (Relaxation)

```
relaxation.vasp.hse-warren
relaxation.vasp.hse-with-wavecar-warren
relaxation.vasp.hsesol-warren
relaxation.vasp.pbe-metal-warren
relaxation.vasp.pbe-warren
relaxation.vasp.pbesol-warren
relaxation.vasp.pbesol-with-wavecar-warren
relaxation.vasp.scan-warren
```

### VASP (Static Energy)

```
static-energy.vasp.hse-warren
static-energy.vasp.hsesol-warren
static-energy.vasp.pbe-metal-warren
static-energy.vasp.pbe-warren
static-energy.vasp.pbesol-warren
static-energy.vasp.relaxation-static-hse-hse-warren
static-energy.vasp.relaxation-static-pbe-hse-warren
static-energy.vasp.relaxation-static-pbe-pbe-warren
static-energy.vasp.scan-warren
```

### Bader

```
bader.vasp-baderkit.bader-warren
```

### BadELF

```
badelf.vasp-baderkit.spin-badelf-hse-warren
badelf.vasp-baderkit.spin-badelf-pbesol-warren
```

### ElfLabeler

```
elf-analysis.vasp-baderkit.elf-radii-warren
elf-analysis.vasp-baderkit.spin-elf-analysis-warren
```

--------------------------------------------------------------------------------

## Helpful Resources

 - [Scott Warren](https://chem.unc.edu/faculty/warren-scott/) (UNC contact page)
 - [Lab Website](https://materials-lab.io/)

--------------------------------------------------------------------------------
