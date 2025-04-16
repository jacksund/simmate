# Enamine

## About

!!! quote

    *Encompassing REAL and Freedom Spaces, [Enamine] boasts over 50 billion accessible molecules. It serves as an ideal platform for efficient hit finding and exploration – from uncovering previously unknown starting points for your discovery projects to rapid hit expansion and optimization using cutting-edge technologies in Computational Chemistry, Bioinformatics, and Machine Learning.*

 - [Enamine Website](https://chem-space.com/)
 - [Enamine Web Search](https://chem-space.com/search)
 - [Enamine Downloads](https://chem-space.com/compounds)

--------------------------------------------------------------------------------

## About this App

Simmate's `enamine` app helps to download Enamine data & load it into the Simmate database.

| Module                 | CLI                      | Workflows                | Data               |
| ---------------------- | ------------------------ | ------------------------ | ------------------ |
| `simmate.apps.enamine` | :heavy_multiplication_x: | :heavy_multiplication_x: | :heavy_check_mark: |

--------------------------------------------------------------------------------

## Installation

1. Add `enamine` to the list of installed Simmate apps with:
``` bash
simmate config add enamine
```

2. Ensure everything is configured correctly:
``` shell
simmate config test enamine
```

3. Add new tables to your database:
``` shell
simmate database update
```

4. Download all ChEMBL datasets:
``` shell
simmate database download enamine
```

--------------------------------------------------------------------------------

## Datasets

| Dataset        | Disk Space | Rows (#) | SQL Table                  | Python Class          |
| -------------- | ---------- | -------- | -------------------------- | --------------------- |
| REAL Molecules | ---        | ---      | `enamine__real__molecules` | `EnamineRealMolecule` |

!!! tip
    Read through [our database guide](/full_guides/database/basic_use.md) to learn how to work with these datasets

!!! example

    === "python"
        ``` python
        from simmate.database import connect
        from simmate.apps.enamine.models import EnamineFreedomSpaceMolecule

        mol_sample_data = EnamineFreedomSpaceMolecule.objects.to_dataframe(limit=5_000)
        ```

--------------------------------------------------------------------------------
