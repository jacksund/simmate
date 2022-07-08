
Overview
========

This module downloads data from third-parties and stores it to your local database.

This data is **NOT** from the Simmate team. These providers are independent groups, and you should cite them appropriately. All data from these providers remain under their source's terms and conditions.

Currently, we support the following providers:

- [COD (Crystallography Open Database)](http://www.crystallography.net/cod/)
- [JARVIS (Joint Automated Repository for Various Integrated Simulations)](https://jarvis.nist.gov/)
- [Materials Project](https://materialsproject.org/)
- [OQMD (Open Quantum Materials Database)](http://oqmd.org/)

These providers are configured, but our team is waiting for permission to redistribute their data:

- [AFLOW (Automatic FLOW for Materials Discovery)](http://www.aflowlib.org/)


Contributing your data
======================

If your team would like to make data available via Simmate, please see the `simmate.database.third_parties.for_providers` module. Even if its is a single table, don't hesistate to make a contribution! We outline the benefits of contributing and how to package your data within the `for_providers` module.


Usage
======

Make sure you have completed [our introductory tutorial](https://github.com/jacksund/simmate/blob/main/tutorials/05_Search_the_database.md) for downloading data from these providers. Below we show example usage with `MatprojStructure`, but the same process can be done with all other tables in this module. 

WARNING: The first time you load archives of data, it can take a long time, so we recommend running some things overnight. Once completed, we also recommend backing up your database (by making a copy of your ~/simmate/my_env-database.sqlite3 file). This ensures you don't have to repeat this long process.

To download all data into your database:

``` python
from simmate.database.third_parties import MatprojStructure

# This can take >1 hour for some providers. Optionally, you can
# add `parallel=True` to speed up this process, but use caution when 
# parallelizing with SQLite (the default backend). We recommend 
# avoiding the use of parallel=True, and instead running
# this line overnight.
MatprojStructure.load_remote_archive()

# If you use this providers data, be sure to cite them!
MatprojStructure.source_doi
```

Some database providers give a calculated energy, which can be used to populate stability information:

``` python
# updates ALL chemical systems.
# Note, this can take over an hour for some providers. Try running 
# this overnight along with your call to load_remote_archive.
MatprojStructure.update_all_stabilities()

# updates ONE chemical system
# This can be used if you quickly want to update a specific system
MatprojStructure.update_chemical_system_stabilities("Y-C-F")
```

See `simmate.database` docs for a guide on filtering results and converting to toolkit/dataframes.


Alternatives
============

This module can be viewed as an alternative to and/or an extension of the following codes:

- [MPContribs](https://github.com/materialsproject/MPContribs)
- [matminer.data_retrieval](https://matminer.readthedocs.io/en/latest/matminer.data_retrieval.html)
- [pymatgen.ext](https://pymatgen.org/pymatgen.ext.html)
- [OPTIMADE APIs](http://www.optimade.org/)

This module stores data locally and then allows rapidly loading data to memory, whereas alternatives involve querying external APIs and loading data into memory. We choose to store data locally because it allows stability (i.e. no breaking changes in your source data) and fast loading accross python sessions. This is particullary useful for high-throughput studies.
