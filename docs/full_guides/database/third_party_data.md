# Accessing Third-party Data

This module simplifies the process of downloading data from external providers and storing it in your local database.

Please be aware that this data is **NOT** provided by the Simmate team. The providers are separate entities and should be properly credited. All data is subject to the respective provider's terms and conditions.

We currently support data from these providers:

- [x] [COD (Crystallography Open Database)](http://www.crystallography.net/cod/)
- [x] [JARVIS (Joint Automated Repository for Various Integrated Simulations)](https://jarvis.nist.gov/)
- [x] [Materials Project](https://materialsproject.org/)
- [x] [OQMD (Open Quantum Materials Database)](http://oqmd.org/)

We have also configured the following provider, but are still awaiting permission to redistribute their data:

- [ ] [AFLOW (Automatic FLOW for Materials Discovery)](http://www.aflowlib.org/)

!!! tip
    If you're interested in making your data accessible via Simmate, please refer to the Contributing data module. We welcome contributions of any size! The `for_providers` module provides more information on the benefits of contributing and how to package your data.

----------------------------------------------------------------------

## Downloading Data

Before proceeding, make sure you've completed [our introductory tutorial](/simmate/getting_started/access_the_database/access_thirdparty_data/) on downloading data from these providers. We use `MatprojStructure` as an example, but the same procedure applies to all other tables in this module.

WARNING: The initial loading of the data archive can be time-consuming. We suggest running this process overnight. Once completed, we recommend backing up your database by duplicating your ~/simmate/my_env-database.sqlite3 file to avoid repeating this lengthy process.

To download all data into your database:

```shell
simmate database load-remote-archives
```

Or in Python, you can download a specific table:

``` python
from simmate.database.third_parties import MatprojStructure

# This process can take >1 hour for some providers. You can
# add `parallel=True` to expedite this process, but exercise caution when 
# parallelizing with SQLite (the default backend). We recommend 
# avoiding the use of parallel=True, and instead running
# this line overnight.
MatprojStructure.load_remote_archive()

# Remember to cite the provider if you use their data!
MatprojStructure.source_doi
```

----------------------------------------------------------------------

## Updating Energy Fields

Some database providers offer calculated energy, which can be used to update stability information:

``` python
# updates ALL chemical systems.
# This process can take over an hour for some providers. Consider running 
# this overnight along with your call to load_remote_archive.
MatprojStructure.update_all_stabilities()

# updates ONE chemical system
# Use this if you need to quickly update a specific system
MatprojStructure.update_chemical_system_stabilities("Y-C-F")
```

----------------------------------------------------------------------

## Alternative Options

This module can be used as an alternative or in addition to the following codes:

- [MPContribs](https://github.com/materialsproject/MPContribs)
- [matminer.data_retrieval](https://matminer.readthedocs.io/en/latest/matminer.data_retrieval.html)
- [pymatgen.ext](https://pymatgen.org/pymatgen.ext.html)
- [OPTIMADE APIs](http://www.optimade.org/)

Unlike alternatives that query external APIs and load data into memory, this module stores data locally for quick loading in future Python sessions. This method ensures data stability (i.e., no unexpected changes in your source data) and fast loading, which is especially useful for high-throughput studies.

----------------------------------------------------------------------