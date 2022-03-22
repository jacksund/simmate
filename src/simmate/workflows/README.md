Simmate Workflows
=================

This module brings together all predefined workflows and organizes them by application for convenience.


Usage
======

[Tutorials 01-05](https://github.com/jacksund/simmate/tree/main/tutorials) will teach you how to run workflows and access their results. But as a review:

``` python
from simmate.workflows.static_energy import mit_workflow

# runs the workflow and returns a status
status = mit_workflow.run(structure=...)

# gives the DatabaseTable where ALL results are stored
mit_workflow.result_table
```


Location of Each Workflow's Source-code
=======================================

The code that defines these workflows and configures their settings are located in the corresponding `simmate.calculators` module. We make workflows accessible here because users often want to search for workflows by application -- not by their calculator name. For example, a structure relaxation that uses VASP under MIT project settings can be imported with...

``` python
from simmate.workflows.relaxation import mit_workflow
```

Alternatively, this same workflow could have been imported with...

``` python
from simmate.calculators.vasp.workflows.relaxation import mit_workflow
```
