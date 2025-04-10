# eMolecules

!!! warning
    While the Simmate app is free, eMolecules has a catalog of free and paid datasets -- both of which require you to make an account on their website. Our app is configured to use the free datasets by default. However, you must download these datasets through your personal account as Simmate cannot automate the download for you.


## About

!!! quote

    *Instant access to the molecules you need. The world’s largest in-stock chemical space at your finger tips. Faster, more reliable delivery to hit your timelines. Services and capabilities to drive compound procurement and management efficiencies throughout the drug discovery research process. It all adds up to eMolecules, your partner for gaining advantage..*

 - [eMolecules Website](https://chem-space.com/)
 - [eMolecules Web Search](https://search.emolecules.com/)
 - [eMolecules Downloads](https://www.emolecules.com/data-downloads)

--------------------------------------------------------------------------------

## About this App

Simmate's `emolecules` app helps to download eMolecules data & load it into the Simmate database.

| Module                    | CLI                      | Workflows                | Data               |
| ------------------------- | ------------------------ | ------------------------ | ------------------ |
| `simmate.apps.emolecules` | :heavy_multiplication_x: | :heavy_multiplication_x: | :heavy_check_mark: |

--------------------------------------------------------------------------------

## Installation

1. Add `emolecules` to the list of installed Simmate apps with:
``` bash
simmate config add emolecules
```

2. Ensure everything is configured correctly:
``` shell
simmate config test emolecules
```

3. Add new tables to your database:
``` shell
simmate database update
```

4. Download all eMolecules datasets:
``` shell
simmate database download emolecules
```

--------------------------------------------------------------------------------

## Datasets

| Dataset         | Disk Space | Rows (#) | SQL Table                     | Python Class              |
| --------------- | ---------- | -------- | ----------------------------- | ------------------------- |
| Molecules       | ---        | ---      | `emolecules__molecules`       | `EmoleculesMolecule`      |
| Supplier Offers | ---        | ---      | `emolecules__supplier_offers` | `EmoleculesSupplierOffer` |

!!! tip
    Read through [our database guide](/full_guides/database/basic_use.md) to learn how to work with these datasets

!!! example

    === "python"
        ``` python
        from simmate.database import connect
        from simmate.apps.emolecules.models import EmoleculesMolecule, EmoleculesSupplierOffer

        mol_sample_data = EmoleculesMolecule.objects.to_dataframe(limit=5_000)
        offer_sample_data = EmoleculesSupplierOffer.objects.to_dataframe(limit=5_000)
        ```

--------------------------------------------------------------------------------
