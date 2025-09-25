# The Pesticide Properties DataBase

!!! warning
    While the Simmate app is free, [a license is required to download PPDB data](https://sitem.herts.ac.uk/aeru/ppdb/en/purchase_database.htm). For this reason, Simmate does *NOT* redistribute any of their data -- instead, you must purchase a license and their raw data from PPDB directly. Also note that Simmate is *NOT* associated with the PPDB. Proceed with caution.


## About

!!! quote

    *The PPDB is a comprehensive relational database of pesticide chemical identity, physicochemical, human health and ecotoxicological data. It also contains data for other related substances such as adjuvants, biostimulants and wood preservatives. It has been developed by the Agriculture & Environment Research Unit (AERU) at the University of Hertfordshire for a variety of end users to support risk assessments and risk management.*

 - [PPDB Website](https://sitem.herts.ac.uk/aeru/ppdb/en/index.htm)
 - [PPDB Full Index](https://sitem.herts.ac.uk/aeru/ppdb/en/atoz.htm)
 - [PPDB Purchasing & Licensing](https://sitem.herts.ac.uk/aeru/ppdb/en/purchase_database.htm)

--------------------------------------------------------------------------------

## About this App

Simmate's `ppdb` app helps to download PPDB data & load it into the Simmate database.

| Module              | CLI                      | Workflows                | Data               |
| ------------------- | ------------------------ | ------------------------ | ------------------ |
| `simmate.apps.ppdb` | :heavy_multiplication_x: | :heavy_multiplication_x: | :heavy_check_mark: |

--------------------------------------------------------------------------------

## Installation

1. Add `ppdb` to the list of installed Simmate apps with:
``` bash
simmate config add ppdb
```

2. Ensure everything is configured correctly:
``` shell
simmate config test ppdb
```

3. Add new tables to your database:
``` shell
simmate database update
```

4. Download all PDB datasets:
``` shell
simmate database download ppdb
```

--------------------------------------------------------------------------------

## Datasets

| Dataset          | Disk Space | Rows (#) | SQL Table         | Python Class    |
| ---------------- | ---------- | -------- | ----------------- | --------------- |
| Molecules        | ---        | ---      | `ppdb__molecules` | `PpdbMolecule`  |

!!! tip
    Read through [our database guide](/full_guides/database/basic_use.md) to learn how to work with these datasets

!!! example

    === "python"
        ``` python
        from simmate.database import connect
        from simmate.apps.ppdb.models import PpdbMolecule

        mol_sample_data = PpdbMolecule.objects.to_dataframe(limit=5_000)
        ```

--------------------------------------------------------------------------------
