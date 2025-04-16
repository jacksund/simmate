# ChEMBL

## About

The ChEMBL Database:


!!! quote

    *ChEMBL is a manually curated database of bioactive molecules with drug-like properties. It brings together chemical, bioactivity and genomic data to aid the translation of genomic information into effective new drugs.*

 - [ChEMBL Website](https://www.ebi.ac.uk/chembl/)
 - [ChEMBL Web Search](https://www.surechembl.org/)
 - [ChEMBL Downloads](https://chembl.gitbook.io/chembl-interface-documentation/downloads)

--------------------------------------------------------------------------------

## About this App

Simmate's `chembl` app helps to download The ChEMBL Database data & load it into the Simmate database.

| Module                | CLI                      | Workflows                | Data               |
| --------------------- | ------------------------ | ------------------------ | ------------------ |
| `simmate.apps.chembl` | :heavy_multiplication_x: | :heavy_multiplication_x: | :heavy_check_mark: |

--------------------------------------------------------------------------------

## Installation

1. Add `chembl` to the list of installed Simmate apps with:
``` bash
simmate config add chembl
```

2. Ensure everything is configured correctly:
``` shell
simmate config test chembl
```

3. Add new tables to your database:
``` shell
simmate database update
```

4. Download all ChEMBL datasets:
``` shell
simmate database download chembl
```

--------------------------------------------------------------------------------

## Datasets

| Dataset          | Disk Space | Rows (#) | SQL Table               | Python Class        |
| ---------------- | ---------- | -------- | ----------------------- | ------------------- |
| Molecules        | ---        | ---      | `chembl__molecules`     | `ChemblMolecule`    |
| Source Documents | ---        | ---      | `chembl__documents`     | `ChemblDocument`    |
| Molecules        | ---        | ---      | `chembl__assay_results` | `ChemblAssayResult` |

!!! tip
    Read through [our database guide](/full_guides/database/basic_use.md) to learn how to work with these datasets

!!! example

    === "python"
        ``` python
        from simmate.database import connect
        from simmate.apps.chembl.models import (
            ChemblMolecule,
            ChemblDocument,
            ChemblAssayResult,
        )

        mol_sample_data = ChemblMolecule.objects.to_dataframe(limit=5_000)
        doc_sample_data = ChemblDocument.objects.to_dataframe(limit=5_000)
        assay_sample_data = ChemblAssayResult.objects.to_dataframe(limit=5_000)
        ```

--------------------------------------------------------------------------------
