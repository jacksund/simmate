# Basic App Use

## Finding & Installing Apps

1. Browse the full list in the [`Apps`](/apps/overview.md) tab above :material-arrow-up::material-arrow-up::material-arrow-up:

2. Follow the installation directions for each app you would like to use

## Install **_all_** available apps

!!! danger
    **This guide is not yet available.** For now, go through each app installation one at a time. We will eventually add a guide on how to install all of them at once, which will help advanced users setup productions systems quickly.

## View installed apps

Run the command:

``` bash
simmate config show
```

And in the output, your list of installed app configs will be shown under the `apps` key:

``` bash
# example output
apps:
- simmate.apps.configs.QuantumEspressoConfig
- simmate.apps.configs.VaspConfig
- simmate.apps.configs.BaderConfig
- simmate.apps.configs.EvolutionConfig
- simmate.apps.configs.MaterialsProjectConfig
- simmate.apps.configs.AflowConfig
- simmate.apps.configs.CodConfig
- simmate.apps.configs.JarvisConfig
- simmate.apps.configs.OqmdConfig
```

## Uninstall an app

!!! warning
    Removing an app does **not** remove its tables from your database.

Go to your `~/simmate/settings.yaml` file, and remove the target config(s) from the `apps:` list.


## Accessing tables

:material-arrow-left::material-arrow-left::material-arrow-left: refer to [our database guide](/full_guides/workflows/basic_use.md) in the sidebar for basic use.

All of an app's tables and datasets are packaged within its `models` module, such as `simmate.apps.example.models`. This is because Simmate uses [Django ORM](https://docs.djangoproject.com/en/5.1/topics/db/queries/) under the hood, and following with their terminology, a `model` is effectively the definition of a single database table.

!!! example
    We can then load the Materials Project structures table from `simmate.apps.materials_project.models`:

    ``` python
    from simmate.apps.materials_project.models import MatprojStructure
    ```

## Accessing workflows

:material-arrow-left::material-arrow-left::material-arrow-left: refer to [our workflows guide](/full_guides/workflows/basic_use.md) in the sidebar for basic use.

In addition, advanced python users may choose to import a workflow directly (rather than use the `get_workflow` utility). All of an app's workflows are packaged within its `workflow` module, such as `simmate.apps.example.workflows`.

!!! example
    `static-energy.vasp.mat-proj` is converted to `StaticEnergy__Vasp__MatProj` following [our workflow naming conventions](/full_guides/workflows/naming_conventions.md). We can then pull this workflow class from `simmate.apps.materials_project.workflows`:

    ``` python
    from simmate.apps.materials_project.workflows import StaticEnergy__Vasp__MatProj
    ```
