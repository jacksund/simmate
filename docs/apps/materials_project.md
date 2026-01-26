# The Materials Project

## About

The Materials Project:

!!! quote
    *The Materials Project is a multi-institution, multi-national effort to compute the properties of all inorganic materials and provide the data and associated analysis algorithms for every materials researcher free of charge. The ultimate goal of the initiative is to drastically reduce the time needed to invent new materials by focusing costly and time-consuming experiments on compounds that show the most promise computationally.*

- [Materials Project website](https://next-gen.materialsproject.org/)
- [`pymatgen` website](https://pymatgen.org/index.html)
- [`atomate` website](https://atomate.org/)

--------------------------------------------------------------------------------

## About this App

Simmate's `materials_project` app...

- helps to download Materials Project data & load it into the Simmate database
- provides many workflows & error handlers from [`pymatgen`](https://pymatgen.org/index.html) and [`atomate`](https://atomate.org/)

*NOTE: our Simmate workflows are full reimplementations of Materials Project workflows*

| Module                           | CLI                      | Workflows          | Data               |
| -------------------------------- | ------------------------ | ------------------ | ------------------ |
| `simmate.apps.materials_project` | :heavy_multiplication_x: | :heavy_check_mark: | :heavy_check_mark: |

--------------------------------------------------------------------------------

## Installation

1. Add `materials_project` to the list of installed Simmate apps with:
``` bash
simmate config add materials_project
```

1. (optional) For Bader workflows, make sure you have the Bader command (from the Henkleman group) installed using one of two options:
      - (*for beginners*) Install [Docker-Desktop](https://www.docker.com/products/docker-desktop/). Then run the following command:
          ``` bash
          simmate config update "bader.docker.enable=True"
          ```
      - (*for experts*) Install Bader using [offical guides](http://theory.cm.utexas.edu/henkelman/code/bader/) and make sure `bader` is in the path

2. (optional) For VASP workflows, make sure you have the `vasp_std` command installed using one of two options:
      - (*for beginners*) Install [Docker-Desktop](https://www.docker.com/products/docker-desktop/). Then run the following commands:
          ``` bash
          simmate config update "vasp.docker.enable=True"
          simmate config update "vasp.docker.image=example.com:vasp/latest"
          ```

        !!! danger
            VASP is a commercial software, so we cannot provide Docker images for it. This is why you must provide a private image via `image=example.com:vasp/latest`.

      - (*for experts*) Install VASP using [offical guides](https://www.vasp.at/) and make sure `vasp_std` is in the path

3. Add new tables to your database:
``` shell
simmate database update
```

1. Ensure everything is configured correctly:
``` shell
simmate config test materials_project
```

1. Download all Materials Project datasets:
``` shell
simmate database download materials_project
```

--------------------------------------------------------------------------------

## Datasets

| Dataset    | Disk Space | Rows (#) | SQL Table                       | Python Class       |
| ---------- | ---------- | -------- | ------------------------------- | ------------------ |
| Structures | ---        | ---      | `materials_project__structures` | `MatprojStructure` |

!!! tip
    Read through [our database guide](/full_guides/database/basic_use.md) to learn how to work with these datasets

!!! example

    === "python"
        ``` python
        from simmate.database import connect
        from simmate.apps.materials_project.models import MatprojStructure

        mp_sample_data = MatprojStructure.objects.to_dataframe(limit=5_000)
        ```

--------------------------------------------------------------------------------

## Workflows

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

!!! tip
    Read through [our workflow guide](/full_guides/workflows/basic_use.md) to learn how to run workflows

!!! example

    === "python"
        ``` python
        from simmate.workflows.utilities import get_workflow

        workflow_name = "static-energy.vasp.matproj"
        workflow = get_workflow(workflow_name)
        
        result = workflow.run(structure="my_example.cif")  # replace with your own file
        ```

--------------------------------------------------------------------------------
