# OQMD

## About

!!! quote

    *The OQMD is a database of DFT calculated thermodynamic and structural properties of [>1,200,000] materials, created in Chris Wolverton's group at Northwestern University.*


 - [OQMD Website](https://chem-space.com/)

--------------------------------------------------------------------------------

## About this App

Simmate's `oqmd` app helps to download OQMD data & load it into the Simmate database.

| Module              | CLI                      | Workflows                | Data               |
| ------------------- | ------------------------ | ------------------------ | ------------------ |
| `simmate.apps.oqmd` | :heavy_multiplication_x: | :heavy_multiplication_x: | :heavy_check_mark: |

--------------------------------------------------------------------------------

## Installation

1. Add `oqmd` to the list of installed Simmate apps with:
``` bash
simmate config add oqmd
```

2. Ensure everything is configured correctly:
``` shell
simmate config test oqmd
```

3. Add new tables to your database:
``` shell
simmate database update
```

4. Download all OQMD datasets:
``` shell
simmate database download oqmd
```

--------------------------------------------------------------------------------

## Datasets

| Dataset           | Disk Space | Rows (#) | SQL Table          | Python Class    |
| ----------------- | ---------- | -------- | ------------------ | --------------- |
| Freedom Molecules | ---        | ---      | `oqmd__structures` | `OqmdStructure` |

!!! tip
    Read through [our database guide](/full_guides/database/basic_use.md) to learn how to work with these datasets

!!! example

    === "python"
        ``` python
        from simmate.database import connect
        from simmate.apps.oqmd.models import OqmdStructure

        oqmd_sample_data = OqmdStructure.objects.to_dataframe(limit=5_000)
        ```

--------------------------------------------------------------------------------
