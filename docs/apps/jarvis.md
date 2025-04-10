# JARVIS

## About

!!! quote

    *Encompassing REAL and Freedom Spaces, [JARVIS] boasts over 50 billion accessible molecules. It serves as an ideal platform for efficient hit finding and exploration – from uncovering previously unknown starting points for your discovery projects to rapid hit expansion and optimization using cutting-edge technologies in Computational Chemistry, Bioinformatics, and Machine Learning.*

 - [JARVIS Website](https://chem-space.com/)
 - [JARVIS Web Search](https://chem-space.com/search)
 - [JARVIS Downloads](https://chem-space.com/compounds)

--------------------------------------------------------------------------------

## About this App

Simmate's `jarvis` app helps to download JARVIS data & load it into the Simmate database.

| Module                | CLI                      | Workflows                | Data               |
| --------------------- | ------------------------ | ------------------------ | ------------------ |
| `simmate.apps.jarvis` | :heavy_multiplication_x: | :heavy_multiplication_x: | :heavy_check_mark: |

--------------------------------------------------------------------------------

## Installation

1. Add `jarvis` to the list of installed Simmate apps with:
``` bash
simmate config add jarvis
```

2. Ensure everything is configured correctly:
``` shell
simmate config test jarvis
```

3. Add new tables to your database:
``` shell
simmate database update
```

4. Download all JARVIS datasets:
``` shell
simmate database download jarvis
```

--------------------------------------------------------------------------------

## Datasets

| Dataset           | Disk Space | Rows (#) | SQL Table            | Python Class      |
| ----------------- | ---------- | -------- | -------------------- | ----------------- |
| Freedom Molecules | ---        | ---      | `jarvis__structures` | `JarvisStructure` |

!!! tip
    Read through [our database guide](/full_guides/database/basic_use.md) to learn how to work with these datasets

!!! example

    === "python"
        ``` python
        from simmate.database import connect
        from simmate.apps.jarvis.models import JarvisStructure

        jarvis_sample_data = JarvisStructure.objects.to_dataframe(limit=5_000)
        ```

--------------------------------------------------------------------------------
