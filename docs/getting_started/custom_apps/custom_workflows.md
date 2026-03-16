# Custom Workflows

A **Simmate Workflow** is essentially a Python function with extra functionality. You can create workflows as standalone scripts or as part of a Simmate App.

-------------------------------------------------------------------------------

## The `@workflow` Decorator

The simplest way to create a workflow is by adding the `@workflow` decorator to a function. This decorator automatically handles:

1. Generating a unique ID (`run_id`) for each run.
2. Creating a dedicated folder (`directory`) for the calculation.
3. Automatically converting inputs (like file paths) into Python objects.
4. Logging the start and end times.

### Basic Workflow Example

``` python
from simmate.workflows import workflow

@workflow
def add_numbers(x, y, **kwargs):
    print(f"I'm running in folder: {kwargs['directory']}")
    return x + y

# Run the workflow
result = add_numbers.run(x=1, y=2)
```

!!! note "Why use `**kwargs`?"
    We always include `**kwargs` in our workflow functions. This is because Simmate passes extra information (like `run_id` and `directory`) that you might want to use inside your function.

-------------------------------------------------------------------------------

## Class-Based Workflows

While the decorator is easy, **Class-Based Workflows** are more powerful and are used for production-grade projects. They allow you to:

- Create "base" workflows with common settings (e.g., VASP PBE).
- Subclass existing workflows to make small tweaks (e.g., VASP PBE with higher ENCUT).
- Organize complex logic more effectively.

### Creating a `Workflow` Class

To create a class-based workflow, inherit from `simmate.workflows.Workflow` and define a `run_config` method.

``` python
from simmate.workflows import Workflow

class Example__Basic__WritePrimitive(Workflow):
    
    use_database = False  # we aren't using a custom table yet

    @staticmethod
    def run_config(structure, directory, **kwargs):
        new_structure = structure.get_primitive_structure()
        new_structure.to(directory / "primitive.cif", fmt="cif")

# Run it
Example__Basic__WritePrimitive.run(structure="POSCAR")
```

-------------------------------------------------------------------------------

## Adding Workflows to Your App

If you created a Simmate App (as shown in the previous section), you should define your workflows in the app's `workflows.py` file.

### 1. Define the workflow
Open your app's `workflows.py` file and add your workflow class or function.

### 2. Register the workflow (Optional)
Simmate can automatically detect workflows in `workflows.py` if you name them correctly and import them into the `__init__.py` file of your app.

-------------------------------------------------------------------------------

## Subclassing Existing Apps

The true power of Simmate comes from subclassing workflows from other apps like VASP or Quantum Espresso.

=== "VASP Example"
    ``` python
    from simmate.apps.vasp.workflows.base import VaspWorkflow

    class Relaxation__Vasp__MyHighPrecision(VaspWorkflow):
        functional = "PBE"
        _incar = dict(
            PREC="Accurate",
            EDIFF=1e-6,
            ENCUT=600,
            NSW=200,
        )
    ```

=== "Quantum Espresso Example"
    ``` python
    from simmate.apps.quantum_espresso.workflows.base import PwscfWorkflow

    class StaticEnergy__QuantumEspresso__MySettings(PwscfWorkflow):
        system = dict(
            ecutwfc__auto="efficiency",
            ecutrho__auto="efficiency",
        )
        psuedo_mappings_set = "SSSP_PBE_EFFICIENCY"
    ```

By using these base classes, you don't have to worry about writing input files or parsing outputs—Simmate handles it all! In the next section, we'll see how to store the results of these workflows in your own database tables.
