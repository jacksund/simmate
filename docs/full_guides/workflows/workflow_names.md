
# Workflow naming conventions


## How we name workflows

All workflow names follow a specific format of `type.calculator.preset`: 

`type`: the type of analysis the workflow is doing (relaxation, static-energy, dynamics, ...)
    
`calculator`: the third party software that the workflow uses to run (vasp, abinit, qe, deepmd, ...)

`preset`: a unique name to identify the settings used (matproj, quality00, my-test-settings,...)

!!! example

    Using the workflow like `static-energy.vasp.matproj` this means that...
    
    - type = static energy (runs a single point energy)
    - calculator = vasp (uses VASP to calculate the energy)
    - preset = matproj  (uses "Materials Project" settings)




## Class name vs. mini name

`type.calculator.preset` is what we see in most cases, but in python, the workflow class name translates to `Type__Calculator__Preset`. All workflows follow this format.

!!! example

    `static-energy.vasp.matproj` --> `StaticEnergy__VASP__MatProj`

Note, when converting a workflow name in python, we need to replace periods with 2 underscores each (`__`) and convert our phrases to
[pascal case](https://khalilstemmler.com/blogs/camel-case-snake-case-pascal-case/). Hyphen (`-`) placement is based off of capital letters.


## Location of a workflow in the website interface

You can follow the naming conventions (described above) to find a workflow in the website interface:

=== "Template URL"
    ```
    https://simmate.org/workflows/{TYPE}/{CALCULATOR}/{PRESET}
    ```

=== "Example"
    ```
    https://simmate.org/workflows/static-energy/vasp/matproj
    ```

## Location of a workflow's source code

The code that defines these workflows and configures their settings are located in the corresponding `simmate.calculators` module. We make workflows accessible here because users often want to search for workflows by application -- not by their calculator name. The source code of a workflow can be found using the naming convention for workflows described above:

=== "Template Python Import"
    ``` python
    from simmate.calculators.{CALCULATOR}.workflows.{TYPE}.{PRESET} import {FULL_NAME}
    ```

=== "Example"
    ``` python
    from simmate.calculators.vasp.workflows.static_energy.matproj import StaticEnergy__Vasp__Matproj
    ```

This is a really long import, but it gives the same workflow as the `get_workflow` utility. We recommend sticking to `get_workflow` because it is the most convienent and easiest to remember. The only reason you'll need to interact with this longer import is to either:

1. Find the source code for a workflow
2. Optimize the speed of your imports (advanced users only)
