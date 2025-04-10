# ChemSpace

## About

!!! quote

    *Encompassing REAL and Freedom Spaces, [ChemSpace] boasts over 50 billion accessible molecules. It serves as an ideal platform for efficient hit finding and exploration – from uncovering previously unknown starting points for your discovery projects to rapid hit expansion and optimization using cutting-edge technologies in Computational Chemistry, Bioinformatics, and Machine Learning.*

 - [ChemSpace Website](https://chem-space.com/)
 - [ChemSpace Web Search](https://chem-space.com/search)
 - [ChemSpace Downloads](https://chem-space.com/compounds)

--------------------------------------------------------------------------------

## About this App

Simmate's `chemspace` app helps to download The ChEMBL Database data & load it into the Simmate database.

| Module                   | CLI                      | Workflows                | Data               |
| ------------------------ | ------------------------ | ------------------------ | ------------------ |
| `simmate.apps.chemspace` | :heavy_multiplication_x: | :heavy_multiplication_x: | :heavy_check_mark: |

--------------------------------------------------------------------------------

## Installation

1. Add `chemspace` to the list of installed Simmate apps with:
``` bash
simmate config add chemspace
```

2. Ensure everything is configured correctly:
``` shell
simmate config test chemspace
```

3. Add new tables to your database:
``` shell
simmate database update
```

4. Download all ChEMBL datasets:
``` shell
simmate database download chemspace
```

--------------------------------------------------------------------------------

## Datasets

| Dataset           | Disk Space | Rows (#) | SQL Table                             | Python Class                    |
| ----------------- | ---------- | -------- | ------------------------------------- | ------------------------------- |
| Freedom Molecules | ---        | ---      | `chemspace__freedom_space__molecules` | `ChemSpaceFreedomSpaceMolecule` |

!!! tip
    Read through [our database guide](/full_guides/database/basic_use.md) to learn how to work with these datasets

!!! example

    === "python"
        ``` python
        from simmate.database import connect
        from simmate.apps.chemspace.models import ChemSpaceFreedomSpaceMolecule

        mol_sample_data = ChemSpaceFreedomSpaceMolecule.objects.to_dataframe(limit=5_000)
        ```

--------------------------------------------------------------------------------
