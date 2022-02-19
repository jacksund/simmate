
Overview
========

This module downloads data from third-parties and stores it to your local database.

This data is **NOT** from the Simmate team. These providers are independent groups, and you should cite them appropriately. All data from these providers remain under their source's terms and conditions.

Currently, we support the following providers:

- [COD (Crystallography Open Database)](http://www.crystallography.net/cod/)
- [JARVIS (Joint Automated Repository for Various Integrated Simulations)](https://jarvis.nist.gov/)
- [Materials Project](https://materialsproject.org/)

These providers are configured, but our team is waiting for permission to redistribute their data:

- [AFLOW (Automatic FLOW for Materials Discovery)](http://www.aflowlib.org/)
- [OQDM (Open Quantum Materials Database)](http://oqmd.org/)


Contributing your data
======================

If your team would like to make data available via Simmate, please see the `simmate.database.third_parties.for_providers` module. Even if its is a single table, don't hesistate to make a contribution! We outline the benefits of contributing and how to package your data within the `for_providers` module.


Usage
======

Make sure you have completed [our introductory tutorial](https://github.com/jacksund/simmate/blob/main/tutorials/05_Search_the_database.md) for downloading data from these providers.

To download all data into your database:

``` python
from simmate.database.third_parties import JarvisStructure

# this can take >10 min. for some providers
JarvisStructure.load_remote_archive()

# If you use this providers data, be sure to cite them!
Jarvis.source_doi
```

Some database providers give a calculated energy, which can be used to populate stability information:

``` python
# updates ALL chemical systems
# Note, this can take over an hour for some providers
JarvisStructure.update_all_stabilities()

# updates ONE chemical system
# This can be used if you quickly want to update a specific system
JarvisStructure.update_chemical_system_stabilities("Y-C-F")
```

See `simmate.database` docs for a guide on filtering results and converting to toolkit/dataframes.


Alternatives
============

This module can be viewed as an alternative to and/or an extension of the following codes:

- [matminer.data_retrieval](https://matminer.readthedocs.io/en/latest/matminer.data_retrieval.html)
- [pymatgen.ext](https://pymatgen.org/pymatgen.ext.html)
- [OPTIMADE APIs](http://www.optimade.org/)

This module stores data locally and then allows rapidly loading data to memory, whereas alternatives involve querying external APIs and loading data into memory. We choose to store data locally because it allows stability (i.e. no breaking changes in your source data) and fast loading accross python sessions. This is particullary useful for high-throughput studies.
