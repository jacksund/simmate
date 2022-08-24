Local Calculations
=================

Much like the `simmate.workflows` module, this module brings together all database tables that are linked to workflows and organizes them by application for convenience.

Usage
======

[Tutorials 01-05](https://github.com/jacksund/simmate/tree/main/tutorials) will teach you how to run workflows and access their results. But as a review:

``` python
from simmate.workflows.static_energy import mit_workflow

# runs the workflow and returns a status
status = mit_workflow.run(structure=...)

# gives the DatabaseTable where ALL results are stored
mit_workflow.database_table
```

You can also access a table directly with...

``` python
# connects to the database
from simmate.database import connect

from simmate.database.workflow_results import MITStaticEnergy

# NOTE: MITStaticEnergy here is the exact same as database_table in the codeblock
# above this one. These are just two different ways of accessing it.
MITStaticEnergy.objects.filter(...)
```


Location of Each Table's Source-code
=======================================

The code that defines these tables are located in the corresponding `simmate.calculators` module. We make tables accessible here because users often want to search for results by application -- not by their calculator name. For example, the results from all static energy calculations that use VASP under MIT project settings can be imported with...

``` python
from simmate.database.workflow_results import MITStaticEnergy
```

Alternatively, this same database table could have been imported with...

``` python
from simmate.calculators.vasp.database.energy import MITStaticEnergy
```
