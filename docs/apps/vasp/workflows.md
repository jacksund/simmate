## VASP Workflows

!!! warning
    This page is a work-in-progress, as we are still developing guides for defining custom VASP workflows. 

--------------------------------------------------------------------------------

## Available Workflows

!!! note
    This app is meant more so for *building* VASP workflows, rather the *providing* presets. Therefore, many more VASP workflows are available in the `materials_project` and `warren_lab` apps.

```
relaxation.vasp.quality00
relaxation.vasp.quality01
relaxation.vasp.quality02
relaxation.vasp.quality03
relaxation.vasp.quality04
relaxation.vasp.staged
static-energy.vasp.quality04
```

--------------------------------------------------------------------------------

## Making New Workflows

### `VaspWorkflow` base class 

The `VaspWorkflow` class, which includes many built-in features:

=== "basic VASP example"
    ``` python
    from simmate.apps.vasp.workflows.base import VaspWorkflow
    
    class Relaxation__Vasp__MyExample1(VaspWorkflow):
    
        functional = "PBE"
        potcar_mappings = {"Y": "Y_sv", "C": "C"}
    
        _incar = dict(
            PREC="Normal",
            EDIFF=1e-4,
            ENCUT=450,
            NSW=100,
            KSPACING=0.4,
        )
    ```

=== "full-feature VASP example"
    ``` python
    from simmate.apps.vasp.workflows.base import VaspWorkflow
    from simmate.apps.vasp.inputs import PBE_POTCAR_MAPPINGS
    from simmate.apps.vasp.error_handlers import (
        Frozen,
        NonConverging,
        Unconverged,
        Walltime,
    )
    
    
    class Relaxation__Vasp__MyExample2(VaspWorkflow):

        functional = "PBE"
        potcar_mappings = PBE_POTCAR_MAPPINGS  # (1)

        _incar = dict(
            PREC="Normal",  # (2)
            EDIFF__per_atom=1e-5,  # (3)
            ENCUT=450,
            ISIF=3,
            NSW=100,
            IBRION=1,
            POTIM=0.02,
            LCHARG=False,
            LWAVE=False,
            KSPACING=0.4,
            multiple_keywords__smart_ismear={  # (4)
                "metal": dict(
                    ISMEAR=1,
                    SIGMA=0.06,
                ),
                "non-metal": dict(
                    ISMEAR=0,
                    SIGMA=0.05,
                ),
            },
            # WARNING --> see "Custom Modifier"" tab for this to work
            EXAMPLE__multiply_nsites=8,  # (5)
        )
    
        error_handlers = [  # (6)
            Unconverged(),
            NonConverging(),
            Frozen(),
            Walltime(),
        ]
    ```

    1. You can use pre-set mapping for all elements rather than define them yourself
    2. Settings that match the normal VASP input are the same for all structures regardless of composition.
    3. Settings can also be set based on the input structure using built-in tags like `__per_atom`. Note the two underscores (`__`) signals that we are using a input modifier.
    4. The type of smearing we use depends on if we have a metal, semiconductor, or insulator. So we need to decide this using a built-in keyword modifier named `smart_ismear`. Because this handles the setting of multiple INCAR values, the input begins with `multiple_keywords` instead of a parameter name.
    5. If you want to create your own logic for an input parameter, you can do that as well. Here we are showing a new modifier named `multiply_nsites`. This would set the incar value of EXAMPLE=16 for structure with 2 sites (2*8=16). Note, we define how this modifer works and register it in the "Custom INCAR modifier" tab. Make sure you include this code as well.
    6. These are some default error handlers to use, and there are many more error handlers available than what's shown. Note, the order of the handlers matters here. Only the first error handler triggered in this list will be used before restarting the job

=== "Custom INCAR modifier"
      If you need to add advanced logic for one of your INCAR tags, you can register a keyword_modifier to the INCAR class like so:
    ``` python
    # STEP 1: define the logic of your modifier as a function
    # Note that the function name must begin with "keyword_modifier_"
    def keyword_modifier_multiply_nsites(structure, example_mod_input):
        # add your advanced logic to determine the keyword value.
        return structure.num_sites * example_mod_input
    
    # STEP 2: register modifier with the Incar class
    from simmate.apps.vasp.inputs import Incar
    Incar.add_keyword_modifier(keyword_modifier_multiply_nsites)
    
    # STEP 3: use your new modifier with any parameter you'd like
    _incar = dict(
        "NSW__multiply_nsites": 2,
        "EXAMPLE__multiply_nsites": 123,
    )
    ```
    
    !!! danger
        Make sure this code is ran BEFORE you run the workflow. Registration is 
        reset every time a new python session starts. Therefore, we recommend 
        keeping your modifer in the same file that you define your workflow in.

You can also use Python inheritance to borrow utilities and settings from an existing workflow:

``` python
from simmate.workflows.utilities import get_workflow

original_workflow = get_workflow("static-energy.vasp.matproj")


class StaticEnergy__Vasp__MyCustomPreset(original_workflow):

    version = "2022.07.04"

    _incar_updates = dict(
        NPAR=1,
        ENCUT=-1,
    )
```

--------------------------------------------------------------------------------
