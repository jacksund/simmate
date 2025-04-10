# EPPO Global Database

## About

!!! quote

    *EPPO Global Database is maintained by the Secretariat of the European and Mediterranean Plant Protection Organization (EPPO). The aim of the database is to provide all pest-specific information that has been produced or collected by EPPO. The database contents are constantly being updated by the EPPO Secretariat.*

 - [EPPO GD Website](https://gd.eppo.int/)

--------------------------------------------------------------------------------

## About this App

Simmate's `eppo_gd` app helps to download EPPO Global database & load it into the Simmate database.

| Module                 | CLI                      | Workflows                | Data               |
| ---------------------- | ------------------------ | ------------------------ | ------------------ |
| `simmate.apps.eppo_gd` | :heavy_multiplication_x: | :heavy_multiplication_x: | :heavy_check_mark: |

--------------------------------------------------------------------------------

## Installation

1. Add `eppo_gd` to the list of installed Simmate apps with:
``` bash
simmate config add eppo_gd
```

2. Ensure everything is configured correctly:
``` shell
simmate config test eppo_gd
```

3. Add new tables to your database:
``` shell
simmate database update
```

4. Download all EPPO GD datasets:
``` shell
simmate database download eppo_gd
```

--------------------------------------------------------------------------------

## Datasets

| Dataset    | Disk Space | Rows (#) | SQL Table             | Python Class |
| ---------- | ---------- | -------- | --------------------- | ------------ |
| EPPO Codes | ---        | ---      | `eppo_gd__eppo_codes` | `EppoCode`   |

!!! tip
    Read through [our database guide](/full_guides/database/basic_use.md) to learn how to work with these datasets

!!! example

    === "python"
        ``` python
        from simmate.database import connect
        from simmate.apps.eppo_gd.models import EppoCode

        eppo_sample_data = EppoCode.objects.to_dataframe(limit=5_000)
        ```

--------------------------------------------------------------------------------
