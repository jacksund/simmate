# Class-based Workflows

----------------------------------------------------------------------

## Switching to classes

We now know that all workflows are really just python functions (+ some automatic functionality added on top). However, advanced python users will run into trouble here... This is because functions are not as powerful as classes when it comes to organizing and reusing code.

Simmate therefore let's you build workflows from a `Workflow` class, rather than the `@workflow` function decorator. In order to convert our function to a `Workflow` class, we must do the following:

- set the class name using Simmate conventions *(we cover this in the next section)*
- define a `run_config` method
- add `@staticmethod` or `@classmethod` to `run_config`


Taking our `add` workflow from the previous tutorial:

``` python
from simmate.workflows import Workflow

class Math__Basic__Add(Workflow):

    use_database = False  # we don't have a database table yet

    @staticmethod
    def run_config(x, y, **kwargs):
        return x + y

# running is the same as before
result = Math__Basic__Add.run(x=1, y=2)
```

Nothing has changed with our workflow -- it just looks a little more complex. Writing workflows in this way might seem silly at first, but class-based workflows make advanced features MUCH easier to implement. 

We will demonstrate this in the `App-based Workflows` section. For now, let's focus on our crazy class name (`Math__Basic__Add`) and why we chose that.

----------------------------------------------------------------------

## Naming Your Workflows

### Importance of naming

In Simmate, the naming of your new workflow is a crucial step. 

Certain features, such as the website interface, necessitate that workflow names adhere to a specific format. This allows us to perform tasks such as locating your new workflow within the website interface. We follow a set of rules to generate workflow names like `relaxation.vasp.mit`.

Here's how a workflow name appears in different contexts:

=== "Readable Name"
    ```
    static-energy.vasp.matproj
    ```

=== "Website URL"
    ```
    https://simmate.org/workflows/static-energy/vasp/matproj
    ```

=== "Python Class Name"
    ```
    StaticEnergy__Vasp__Matproj
    ```

!!! example
    `Math__Basic__Add` becomes `math.basic.add`, and once placed in a custom app, this workflow can be found in the website at `http://localhost:8000/workflows/math/basic/add`

### Understanding conventions

Simmate's naming conventions consist of three components:

1.  The type of analysis the workflow performs
2.  The "app" (or program) that the workflow uses for execution
3.  A unique name to distinguish the settings used

Examples for each component are:

1. relaxation, static-energy, dynamics, ...
2. vasp, abinit, qe, deepmd, ...
3. jacks-test, matproj, quality00, ...

Combined, example workflow names would be:

- `relaxation.vasp.jacks-test`
- `static-energy.abinit.matproj`
- `dynamics.qe.quality00`

To convert this to our workflow name in python, we replace periods with two underscores each and convert our words to [pascal case](https://khalilstemmler.com/blogs/camel-case-snake-case-pascal-case/). For instance, our workflow names become:

- `Relaxation__Vasp__JacksTest`
- `StaticEnergy__Abinit__Matproj`
- `Dynamics__Qe__Quality00`

!!! warning
    Be mindful of capitalization as it is crucial in this context. Always double-check your workflow names.

----------------------------------------------------------------------

## Powerful App-based Workflows

Using the `Workflow` organization instead `@workflow` decorator might seem silly at first, but class-based workflows make advanced features MUCH easier to implement. 

For example, say we want to make a workflow that uses Quantum Espresso or VASP. For VASP, we provide a `VaspWorkflow` class. For Quantum Espresso, we provide a `PwscfWorkflow` (PW-SCF is a component of QE). Here are some basic VASP and QE workflows written in Simmate:

=== "VASP"
    ``` python
    from simmate.apps.vasp.workflows.base import VaspWorkflow

    class Relaxation__Vasp__ExampleSettings(VaspWorkflow):

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

=== "Quantum Espresso"
    ``` python
    from simmate.apps.quantum_espresso.workflows.base import PwscfWorkflow

    class StaticEnergy__QuantumEspresso__ExampleSettings(PwscfWorkflow):

        control = dict(
            pseudo_dir__auto=True,
            restart_mode="from_scratch",
            calculation="scf",
            tstress=True,
            tprnfor=True,
        )

        system = dict(
            ibrav=0,
            nat__auto=True,
            ntyp__auto=True,
            ecutwfc__auto="efficiency",
            ecutrho__auto="efficiency",
        )

        electrons = dict(
            diagonalization="cg",
            mixing_mode="plain",
            mixing_beta=0.7,
            conv_thr="1.0e-8",
        )

        psuedo_mappings_set = "SSSP_PBE_EFFICIENCY"

        k_points = dict(
            spacing=0.5,
            gamma_centered=True,
        )
    ```

There are many more workflows and base classes to explore. Be sure to look through both our `Apps` and `Full Guides`.

!!! note
    Even if you don't know how to use VASP or QE, the key takeaway here should be that you can translate their software's inputs into a Simmate workflow with minimal effort.

----------------------------------------------------------------------

## Advanced Workflow Features

There are still many improvements that you may want to incorporate into your new workflow(s). For instance, you might want to:

- [x] Modify a complex workflow (like `diffusion.vasp.neb-all-paths-mit`)
- [x] Develop a custom workflow using a new program such as USPEX or ABINIT
- [x] Utilize a custom database table to store your workflow results
- [x] Access the workflow via the website interface
- [x] Access your workflow from other scripts (and the `get_workflow` function)

These topics will be addressed in the next tutorial, where we will simultaneously cover custom database tables.

----------------------------------------------------------------------

