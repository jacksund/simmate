# Workflows naming conventions

------------------------------------------------------------

## Naming conventions

Every workflow name follows the `type.app.preset` format:

`type`: Defines the type of analysis the workflow carries out (relaxation, static-energy, dynamics, etc.)

`app`: Denotes the third-party software used by the workflow (vasp, abinit, qe, deepmd, etc.)

`preset`: Gives a unique identifier for the settings applied (matproj, quality00, my-test-settings, etc.)

!!! example

    Using `static-energy.vasp.matproj` as an example...
    
    - type = `static` energy (performs a single point energy calculation)
    - app = `vasp` (uses VASP for energy calculation)
    - preset = `matproj`  (implements "Materials Project" settings)

------------------------------------------------------------

## Format in different contexts

Here are several ways workflow names can be represented:

- Basic text: `type.app.preset`
- Python class name: `Type__App__Preset`
- Website URL: `https://simmate.org/workflows/{TYPE}/{APP}/{PRESET}`

When converting a workflow name from basic text to Python, periods should be replaced with double underscores (`__`) and phrases should be converted to [pascal case](https://khalilstemmler.com/blogs/camel-case-snake-case-pascal-case/). The placement of hyphens (`-`) is determined by capital letters.

!!! example
    - `static-energy.vasp.matproj`
    - `StaticEnergy__VASP__MatProj`
    - https://simmate.org/workflows/static-energy/vasp/matproj

------------------------------------------------------------