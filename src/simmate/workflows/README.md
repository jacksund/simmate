# Simmate Workflows

This module brings together all predefined workflows and organizes them by application for convenience.


# Basic use

[Tutorials 01-05](https://github.com/jacksund/simmate/tree/main/tutorials) will teach you how to run workflows and access their results. But as a review:

``` python
from simmate.workflows.all import StaticEnergy__Vasp__Matproj as workflow

# runs the workflow and returns a state
state = workflow.run(structure="my_structure.cif")
result = state.result()

# gives the DatabaseTable where ALL results are stored
workflow.database_table
df = workflow.database_table.objects.to_dataframe()  # convert to pandas dataframe
```

Further information on interacting with workflows can be found in the `simmate.workflow_engine` module as well -- particularly, the `simmate.workflow_engine.workflow` module.


# Workflow naming conventions

All workflow names follow a specific format of `Type__Calculator__Preset` so for an example workflow like `StaticEnergy__Vasp__Matproj` this means that...

- Type = StaticEnergy (workflow runs a single point energy)
- Calculator = Vasp  (workflow uses VASP to calculate the energy)
- Preset = Matproj  (workflow uses "Matproj" type settings in the calculation)

The workflow name can also be used to infer where the workflow is located in python. For `StaticEnergy__Vasp__Matproj`, this corresponds to a name of `static-energy.vasp.matproj` and means the workflow can be accessed in the following ways:

1. `from simmate.workflows.all import StaticEnergy__Vasp__Matproj` (easiest to remember import)
2. `from simmate.workflows.static_energy import StaticEnergy__Vasp__Matproj` (uses the `type`)
3. `from simmate.calculators.vasp.workflows.static_energy.all import StaticEnergy__Vasp__Matproj`  (uses the `type` and `calculator`)
4. `from simmate.calculators.vasp.workflows.static_energy.matproj import StaticEnergy__Vasp__Matproj`  (uses the `type` and `calculator` and `preset`)

These imports all give the same workflow, but we recommend stick to the first option because it is the most convienent and easiest to remember. The only reason you'll need to interact with the other options is to either:

1. Find the source code for a workflow (see section below for more)
2. Optimize the speed of your imports (advanced users only)


<!--
# Location of a workflow in the website interface

You can follow the naming conventions (described above) to find a workflow in the website interface:

```
# Template to use for finding workflows
https://simmate.org/workflows/{TYPE}/{CALCULATOR}/{PRESET}

# Example with StaticEnergy__Vasp__Matproj
https://simmate.org/workflows/static-energy/vasp/matproj
```
-->


# Location of a workflow's source code

The code that defines these workflows and configures their settings are located in the corresponding `simmate.calculators` module. We make workflows accessible here because users often want to search for workflows by application -- not by their calculator name. The source code of a workflow can be found using the naming convention for workflows described above:

``` python
# Template to use for finding workflows
from simmate.calculators.{CALCULATOR}.workflows.{TYPE}.{PRESET} import {FULL_NAME}

# Example with StaticEnergy__Vasp__Matproj
from simmate.calculators.vasp.workflows.static_energy.matproj import StaticEnergy__Vasp__Matproj
```
