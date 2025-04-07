# AFLOW

## About

Automatic FLOW (AFLOW) is "a software framework for high-throughput calculation of crystal structure properties of alloys, intermetallics and inorganic compounds" that is used to generate "a globally available database of 3,530,330 material compounds with over 734,308,640 calculated properties, and growing".

 - [AFLOW Website](https://aflowlib.duke.edu/search/ui/)
 - [AFLOW Paper](https://doi.org/10.1016/j.commatsci.2012.02.005)
 - [AFLOW Prototype Encyclopedia](https://aflowlib.org/prototype-encyclopedia/)

--------------------------------------------------------------------------------

## About this App

Simmate's `aflow` app helps to download AFLOW data & load it into the Simmate database.

| Module               | CLI                      | Workflows                | Data               |
| -------------------- | ------------------------ | ------------------------ | ------------------ |
| `simmate.apps.aflow` | :heavy_multiplication_x: | :heavy_multiplication_x: | :heavy_check_mark: |

--------------------------------------------------------------------------------

## Installation

1. Add `aflow` to the list of installed Simmate apps with:
``` bash
simmate config add aflow
```

2. Ensure everything is configured correctly:
``` shell
simmate config test aflow
```

3. Add new tables to your database:
``` shell
simmate database update
```

4. Download all AFLOW datasets:
``` shell
simmate database download aflow
```

--------------------------------------------------------------------------------

## Datasets

| Dataset    | Disk Space | Rows (#) | SQL Table           | Python Class     |
| ---------- | ---------- | -------- | ------------------- | ---------------- |
| Prototypes | ---        | ---      | `aflow__prototypes` | `AflowPrototype` |
| Structures | ---        | ---      | `aflow__structures` | `AflowStructure` |

!!! tip
    Read through [our database guide](/full_guides/database/basic_use.md) to learn how to work with these datasets

!!! example

    === "python"
        ``` python
        from simmate.database import connect
        from simmate.apps.aflow.models import AflowPrototype, AflowStructure

        prototype_data = AflowPrototype.objects.to_dataframe()

        structures_sample_data = AflowStructure.objects.to_dataframe(limit=5_000)
        ```

--------------------------------------------------------------------------------
