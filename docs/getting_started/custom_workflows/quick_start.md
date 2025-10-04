
# Building custom workflows

!!! warning
    This tutorial only covers workflows that are ran locally. If you are submitting to a cluster via `run_cloud` and/or want advanced features such as the workflow showing in the website UI, you must include your workflow in a custom app. This
    is covered in the next section of tutorials.

## Quick Guide

1. All workflows are really just python functions. Let create a simple python function that adds two numbers together:
```python
def add(x, y):
    return x + y

result = add(x=1, y=2)
```

2. To make this a Simmate workflow, we need to (a) add the `@workflow` decorator and (b) make sure we include `**kwargs` as an input. The `add` function will then become a `Workflow`. This means we have access to a `run` method that adds extra functionality for us and returns a future-like object:
```python
from simmate.workflows import workflow

@workflow
def add(x, y, **kwargs):
    print(f"Extra kwargs: {kwargs}")  # add this new line!
    return x + y

status = add.run(x=1, y=2)
result = status.result()
```

    !!! note
        We added a `print` statement to our function. This was to understand why we require `**kwargs` as an input.
        This print statement will output something similar to:
        ```
        Extra kwargs: {
            'run_id': 'eb467f3e-eb27-4bd0-8600-c49757bc5b63',
            'directory': Path('path/to/simmate-task-abcd1234'),
            'compress_output': False,
            'source': None,
            'started_at': datetime.datetime(2024, 1, 25, 0, 0, 0, 0, tzinfo=datetime.timezone.utc),
        }
        ```

        Thus, the workflow provides optional extra parameters for us to use in our workflow. This includes a new folder (`directory`) that the workflow can use as a scratch space.


1. As more advanced example, here is a workflow that converts a structure to a primitive unitcell and writes it to a CIF file:
    ``` python
    from simmate.workflows import workflow

    @workflow
    def write_primitive(structure, directory, **kwargs):
        new_structure = structure.get_primitive_structure()
        new_structure.to(directory / "primitive.cif", fmt="cif")

    status = write_primitive.run(structure="POSCAR")  # (1)
    result = status.result()
    ```

    1. Note how (a) we provided `POSCAR` (str) but our function converted it to a `toolkit.Structure` object; and (b) we didn't provide a `directory` but Simmate built one for us. Common input parameters adhere to the rules listed in the Parameters section of our documentation.

    !!! tip
        Try out some more advanced examples by going through our Full guides. For example, try running this workflow with...

        ``` python
        status = write_primitive.run(
            structure={
                "database_table": "MatprojStructure",
                "database_id": "mp-123",
            },
            directory="MyNewFolder",
            compress_output=True,
        )
        result = status.result()
        ```

        This pulled our structure from the database, specified the name of the folder we wanted to make, and that we wanted the final folder converted to a `zip` file once it's done.

2. The `@workflow` decorator is very similar to other workflow engines (such as [Prefect](https://www.prefect.io/)). However, the power of Simmate workflows comes from class-based workflows using `Workflow`. This involves some extra code (which at first is very boiler-plate), but we'll explain the signifiance after. Bear with us in the next step :smile:

3. To make a `Workflow` class, we must (i) set the class name using Simmate conventions (see full guides) and (ii) define a `run_config` method as a `@staticmethod` OR a `@classmethod`.
    ``` python
    from simmate.workflows import Workflow

    class Example__Basic__WritePrimitive(Workflow):

        use_database = False  # we don't have a database table yet

        @staticmethod
        def run_config(structure, directory, **kwargs):
            new_structure = structure.get_primitive_structure()
            new_structure.to(directory / "primitive.cif", fmt="cif")
    
    # running is the same as before
    status = Example__Python__WritePrimitive.run(structure="POSCAR")
    result = status.result()
    ```

    !!! note
        The class name is long (and unpythonic), but this how we keep workflows organized. With hundreds of workflows, having an organized format like `static-energy.quantum-espreso.example123` becomes very important. This workflow will give the name `example.basic.write-primitive`

4. This might seem silly at first, but class-based workflows make advanced features MUCH easier to implement. Take for example making workflows using both Quantum Espresso and VASP, which can utilize subclasses of `Workflow`:

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
