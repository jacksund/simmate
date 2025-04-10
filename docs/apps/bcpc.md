# BCPC

## About

The Compendium of Pesticide Common Names (BCPC):


!!! quote

    *This electronic compendium is intended to provide details of the status of all pesticide common names (not just those assigned by ISO), together with their systematic chemical names, molecular formulae, chemical structures and CAS Registry Numbers®. It is designed to function like a database, with several indexes that provide access to the data sheets.*

 - [BCPC Website](http://www.bcpcpesticidecompendium.org/introduction.html)
 - [BCPC Index of Common Names](http://www.bcpcpesticidecompendium.org/index_cn_frame.html)

--------------------------------------------------------------------------------

## About this App

Simmate's `bcpc` app helps to download BCPC data & load it into the Simmate database.

| Module              | CLI                      | Workflows                | Data               |
| ------------------- | ------------------------ | ------------------------ | ------------------ |
| `simmate.apps.bcpc` | :heavy_multiplication_x: | :heavy_multiplication_x: | :heavy_check_mark: |

--------------------------------------------------------------------------------

## Installation

1. Add `bcpc` to the list of installed Simmate apps with:
``` bash
simmate config add bcpc
```

2. Ensure everything is configured correctly:
``` shell
simmate config test bcpc
```

3. Add new tables to your database:
``` shell
simmate database update
```

4. Download all BCPC datasets:
``` shell
simmate database download bcpc
```

--------------------------------------------------------------------------------

## Datasets

| Dataset   | Disk Space | Rows (#) | SQL Table                         | Python Class       |
| --------- | ---------- | -------- | --------------------------------- | ------------------ |
| ISO Names | ---        | ---      | `bcpc__iso_pesticides__molecules` | `BcpcIsoPesticide` |

!!! tip
    Read through [our database guide](/full_guides/database/basic_use.md) to learn how to work with these datasets

!!! example

    === "python"
        ``` python
        from simmate.database import connect
        from simmate.apps.bcpc.models import BcpcIsoPesticide

        pesticides_data = BcpcIsoPesticide.objects.to_dataframe()
        ```

--------------------------------------------------------------------------------
