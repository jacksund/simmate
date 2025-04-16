# The Protein Data Bank

## About

!!! quote

    *Since 1971, the Protein Data Bank archive (PDB) has served as the single repository of information about the 3D structures of proteins, nucleic acids, and complex assemblies.*

 - [PDB Website](https://www.wwpdb.org/)
 - [PDB Ligand Downloads](http://ligand-expo.rcsb.org/ld-download.html)
 - [PDB Archives](https://www.wwpdb.org/ftp/pdb-ftp-sites)

--------------------------------------------------------------------------------

## About this App

Simmate's `pdb` app helps to download PDB data & load it into the Simmate database.

| Module             | CLI                      | Workflows                | Data               |
| ------------------ | ------------------------ | ------------------------ | ------------------ |
| `simmate.apps.pdb` | :heavy_multiplication_x: | :heavy_multiplication_x: | :heavy_check_mark: |

--------------------------------------------------------------------------------

## Installation

1. Add `pdb` to the list of installed Simmate apps with:
``` bash
simmate config add pdb
```

2. Ensure everything is configured correctly:
``` shell
simmate config test pdb
```

3. Add new tables to your database:
``` shell
simmate database update
```

4. Download all PDB datasets:
``` shell
simmate database download pdb
```

--------------------------------------------------------------------------------

## Datasets

| Dataset          | Disk Space | Rows (#) | SQL Table      | Python Class |
| ---------------- | ---------- | -------- | -------------- | ------------ |
| Ligand Molecules | ---        | ---      | `pdb__ligands` | `PdbLigand`  |

!!! tip
    Read through [our database guide](/full_guides/database/basic_use.md) to learn how to work with these datasets

!!! example

    === "python"
        ``` python
        from simmate.database import connect
        from simmate.apps.pdb.models import PdbLigand

        mol_sample_data = PdbLigand.objects.to_dataframe(limit=5_000)
        ```

--------------------------------------------------------------------------------
