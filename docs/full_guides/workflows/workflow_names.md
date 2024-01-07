# Guidelines for Naming Workflows

## Structure for Naming Workflows

Every workflow name follows the `type.app.preset` format:

`type`: Defines the type of analysis the workflow carries out (relaxation, static-energy, dynamics, etc.)

`app`: Denotes the third-party software used by the workflow (vasp, abinit, qe, deepmd, etc.)

`preset`: Gives a unique identifier for the settings applied (matproj, quality00, my-test-settings, etc.)

!!! example

    Take the workflow `static-energy.vasp.matproj` as an example...
    
    - type = static energy (performs a single point energy calculation)
    - app = vasp (uses VASP for energy calculation)
    - preset = matproj  (implements "Materials Project" settings)

------------------------------------------------------------

## Workflow Class Name vs. Mini Name

The `type.app.preset` format is standard, but in Python, the workflow class name is represented as `Type__App__Preset`. All workflows follow this structure.

!!! example

    `static-energy.vasp.matproj` is represented as `StaticEnergy__VASP__MatProj` in Python.

Note that when converting a workflow name in Python, periods should be replaced with double underscores (`__`) and phrases should be converted to [pascal case](https://khalilstemmler.com/blogs/camel-case-snake-case-pascal-case/). The placement of hyphens (`-`) is determined by capital letters.

------------------------------------------------------------

## Finding a Workflow on the Website Interface

You can use the naming conventions described above to find a workflow on the website interface:

=== "Template URL"
    ```
    https://simmate.org/workflows/{TYPE}/{APP}/{PRESET}
    ```

=== "Example"
    ```
    https://simmate.org/workflows/static-energy/vasp/matproj
    ``` 

------------------------------------------------------------