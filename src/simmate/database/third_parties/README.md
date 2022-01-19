
Overview
========

This module downloads data from third-parties and stores it to your local database.

Currently, we support the following providers:

- [AFLOW (Automatic FLOW for Materials Discovery)](http://www.aflowlib.org/)
- [COD (Crystallography Open Database)](http://www.crystallography.net/cod/)
- [JARVIS (Joint Automated Repository for Various Integrated Simulations)](https://jarvis.nist.gov/)
- [Materials Project](https://materialsproject.org/)
- [OQDM (Open Quantum Materials Database)](http://oqmd.org/)

_**WARNING:**_ This data is NOT from the Simmate team. These providers are independent groups, and you should cite them appropriately. All data from these providers remain under their source's terms and conditions.


Usage
======

Make sure you have completed [our introductory tutorial](https://github.com/jacksund/simmate/blob/main/tutorials/05_Search_the_database.md) for downloading data from these providers.

To download all data into your database:

``` python
from simmate.database.third_parties import JarvisStructure

JarvisStructure.load_remote_archive()
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

This module can be viewed as an alternative to / extension of the following codes:

- [matminer.data_retrieval](https://matminer.readthedocs.io/en/latest/matminer.data_retrieval.html)
- [pymatgen.ext](https://pymatgen.org/pymatgen.ext.html)
- [OPTIMADE APIs](http://www.optimade.org/)

This module stores data locally and then allows rapidly loading data to memory, whereas alternatives only load data into memory and involve querying external APIs.
