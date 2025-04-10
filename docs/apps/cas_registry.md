# CAS Registry®

!!! warning
    While the Simmate app is free, [a license is required to use the CAS Registry® API & access their data](https://www.cas.org/services/commonchemistry-api). If you are looking for a free alternative to CAS API, we allow using the [PubChem API](https://pubchem.ncbi.nlm.nih.gov/docs/pug-rest) as the backend for this app, but it comes as the cost of being inaccurate for a small set of CAS Registry Numbers® (<1%). Proceed with caution.

## About

The collection of CAS Registry Numbers®:

!!! quote

    *A CAS Registry Number is a unique and unambiguous identifier for a specific substance that allows clear communication and, with the help of CAS scientists, links together all available data and research about that substance. Governmental agencies rely on CAS Registry Numbers for substance identification in regulatory applications because they are unique, easy validated, and internationally recognized.*

 - [CAS Registry Website](https://www.cas.org/cas-data/cas-registry)
 - [CAS Registry Web Search](https://commonchemistry.cas.org/)
 - [CAS Registry Licensing](https://www.cas.org/services/commonchemistry-api)

--------------------------------------------------------------------------------

## About this App

Simmate's `cas_registry` app helps to download CAS Registry data & load it into the Simmate database. The data is sourced using one of two options:

- **option 1**: from the PubChem API (*the default*)
- **option 2**: from the CAS Registry API (*disabled by default, requires a license*)

For both options, data is loaded *lazily*. This means you must specifically request a CAS Number in order for the related compound data to be downloaded and brought into the Simmate database. We do this because the full CAS database is extremely large (>200 million compounds), making it very expensive to download in full.

| Module                      | CLI                      | Workflows                | Data               |
| --------------------------- | ------------------------ | ------------------------ | ------------------ |
| `simmate.apps.cas_registry` | :heavy_multiplication_x: | :heavy_multiplication_x: | :heavy_check_mark: |

--------------------------------------------------------------------------------

## Installation

1. Add `cas_registry` to the list of installed Simmate apps with:
``` bash
simmate config add cas_registry
```

2. Ensure everything is configured correctly:
``` shell
simmate config test cas_registry
```

3. Add new tables to your database:
``` shell
simmate database update
```

4. Download all CAS datasets:
``` shell
simmate database download cas_registry
```

--------------------------------------------------------------------------------

## Datasets

| Dataset       | Disk Space | Rows (#) | SQL Table                 | Python Class          |
| ------------- | ---------- | -------- | ------------------------- | --------------------- |
| CAS Molecules | ---        | ---      | `cas_registry__molecules` | `CasRegistryMolecule` |

!!! tip
    Read through [our database guide](/full_guides/database/basic_use.md) to learn how to work with these datasets

!!! example

    === "python"
        ``` python
        from simmate.database import connect
        from simmate.apps.cas_registry.models import CasRegistryMolecule

        cas_sample_data = CasRegistryMolecule.objects.to_dataframe(limit=5_000)
        ```

--------------------------------------------------------------------------------
