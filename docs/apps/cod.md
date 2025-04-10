# COD

## About

The Crystallography Open Database (COD):


!!! quote

    *The Crystallography Open Database (COD) is as of the time of writing the largest open-access collection of mineral, metal organic, organometallic, and small organic crystal structures, excluding biomolecules that are stored separately in the Protein Data Bank (PBD).*

 - [COD Website](http://www.bcpcpesticidecompendium.org/introduction.html)
 - [COD Paper](https://doi.org/10.1007/978-3-319-42913-7_66-1)
 - [COD Web Search](https://www.crystallography.net/cod/search.html)

--------------------------------------------------------------------------------

## About this App

Simmate's `cod` app helps to download COD data & load it into the Simmate database.

| Module             | CLI                      | Workflows                | Data               |
| ------------------ | ------------------------ | ------------------------ | ------------------ |
| `simmate.apps.cod` | :heavy_multiplication_x: | :heavy_multiplication_x: | :heavy_check_mark: |

--------------------------------------------------------------------------------

## Installation

1. Add `cod` to the list of installed Simmate apps with:
``` bash
simmate config add cod
```

2. Ensure everything is configured correctly:
``` shell
simmate config test cod
```

3. Add new tables to your database:
``` shell
simmate database update
```

4. Download all COD datasets:
``` shell
simmate database download cod
```

--------------------------------------------------------------------------------

## Datasets

| Dataset    | Disk Space | Rows (#) | SQL Table         | Python Class   |
| ---------- | ---------- | -------- | ----------------- | -------------- |
| Structures | ---        | ---      | `cod__structures` | `CodStructure` |

!!! tip
    Read through [our database guide](/full_guides/database/basic_use.md) to learn how to work with these datasets

!!! example

    === "python"
        ``` python
        from simmate.database import connect
        from simmate.apps.cod.models import CodStructure

        cod_sample_data = CodStructure.objects.to_dataframe()
        ```

--------------------------------------------------------------------------------
