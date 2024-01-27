# The Materials Project Application

--------------------------------------------------------------------------------

## About

From the official [Materials Project website](https://next-gen.materialsproject.org/about):

!!! quote
    *The Materials Project is a multi-institution, multi-national effort to compute the properties of all inorganic materials and provide the data and associated analysis algorithms for every materials researcher free of charge. The ultimate goal of the initiative is to drastically reduce the time needed to invent new materials by focusing costly and time-consuming experiments on compounds that show the most promise computationally.*

Simmate built a `materials_project` app which incorporates workflows used by the Materials Project. This includes preferred DFT settings, dynamic settings, error handlers, and more. Registering this app will introduce numerous new workflow presets that build on several other apps (VASP, Bader, etc.).

!!! note
    This Simmate app is an alternative implementation of the workflows found in [`pymatgen`](https://pymatgen.org/index.html) and [`atomate`](https://atomate.org/).

--------------------------------------------------------------------------------

## Installation

1. Add `materials_project` (and it's dependencies) to the list of installed Simmate apps with:
``` bash
simmate config add materials_project
```

2. For Bader workflows, make sure you have the Bader command (from the Henkleman group) installed using one of two options:
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
simmate config test materials_project
```

--------------------------------------------------------------------------------

## Included Workflows

```
diffusion.vasp.neb-all-paths-mit
diffusion.vasp.neb-from-endpoints-mit
diffusion.vasp.neb-from-images-mit
diffusion.vasp.neb-from-images-mvl-ci
diffusion.vasp.neb-single-path-mit
dynamics.vasp.matproj
dynamics.vasp.mit
dynamics.vasp.mvl-npt
electronic-structure.vasp.matproj-full
electronic-structure.vasp.matproj-hse-full
population-analysis.vasp-bader.bader-matproj
population-analysis.vasp.elf-matproj
relaxation.vasp.matproj
relaxation.vasp.matproj-hse
relaxation.vasp.matproj-hsesol
relaxation.vasp.matproj-metal
relaxation.vasp.matproj-pbesol
relaxation.vasp.matproj-scan
relaxation.vasp.mit
relaxation.vasp.mvl-grainboundary
relaxation.vasp.mvl-neb-endpoint
relaxation.vasp.mvl-slab
static-energy.vasp.matproj
static-energy.vasp.matproj-hse
static-energy.vasp.matproj-hsesol
static-energy.vasp.matproj-pbesol
static-energy.vasp.matproj-scan
static-energy.vasp.mit
static-energy.vasp.mvl-neb-endpoint
static-energy.vasp.prebadelf-matproj
static-energy.vasp.prebader-matproj
```

--------------------------------------------------------------------------------

## Helpful Resources

 - [Materials Project website](https://next-gen.materialsproject.org/)
 - [`pymatgen` website](https://pymatgen.org/index.html)
 - [`atomate` website](https://atomate.org/).

--------------------------------------------------------------------------------
