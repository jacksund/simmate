
# Workflow naming conventions

## How we name workflows

All workflow names follow a specific format of `type.app.preset`:

`type`: the type of analysis the workflow is doing (relaxation, static-energy, dynamics, ...)

`app`: the third party software that the workflow uses to run (vasp, abinit, qe, deepmd, ...)

`preset`: a unique name to identify the settings used (matproj, quality00, my-test-settings,...)

!!! example

    Using the workflow like `static-energy.vasp.matproj` this means that...
    
    - type = static energy (runs a single point energy)
    - app = vasp (uses VASP to calculate the energy)
    - preset = matproj  (uses "Materials Project" settings)

------------------------------------------------------------

## Class name vs. mini name

`type.app.preset` is what we see in most cases, but in python, the workflow class name translates to `Type__App__Preset`. All workflows follow this format.

!!! example

    `static-energy.vasp.matproj` --> `StaticEnergy__VASP__MatProj`

Note, when converting a workflow name in python, we need to replace periods with 2 underscores each (`__`) and convert our phrases to
[pascal case](https://khalilstemmler.com/blogs/camel-case-snake-case-pascal-case/). Hyphen (`-`) placement is based off of capital letters.

------------------------------------------------------------

## Location of a workflow in the website interface

You can follow the naming conventions (described above) to find a workflow in the website interface:

=== "Template URL"
    ```
    https://simmate.org/workflows/{TYPE}/{APP}/{PRESET}
    ```

=== "Example"
    ```
    https://simmate.org/workflows/static-energy/vasp/matproj
    ```

------------------------------------------------------------
