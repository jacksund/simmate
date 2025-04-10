# Accessing Workflow Data

This module, akin to the `simmate.workflows` module, organizes all database tables related to workflows and groups them by application for convenient access.

----------------------------------------------------------------------

## Retrieving Results

[The beginner tutorials](/getting_started/overview.md) offer guidance on running workflows and fetching their results. Here's a brief summary:

``` python
from simmate.workflows.static_energy import mit_workflow

# Runs the workflow and returns a status
status = mit_workflow.run(structure=...)

# Gives the DatabaseTable where ALL results are stored
mit_workflow.database_table
```

You can also directly connect to a table like this...

``` python
# Sets up connection to the database
from simmate.database import connect

from simmate.database.workflow_results import MITStaticEnergy

# NOTE: MITStaticEnergy here is the same as database_table in the previous codeblock.
# These are just two different ways of accessing it.
MITStaticEnergy.objects.filter(...)
```

----------------------------------------------------------------------
