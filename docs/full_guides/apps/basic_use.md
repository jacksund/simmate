# Basic App Use

## Finding & Installing Apps

**Core Apps (Pre-installed)**

Most official Simmate apps (Vasp, Materials Project, etc.) are pre-installed and registered by default. You can start using their workflows and data immediately.

**Custom or Specialized Apps**

1. Browse the full list of apps in the [`Apps`](/apps/overview.md) tab above.
2. If an app is not in your defaults (see below), follow its specific installation directions.

**Restoring Default Apps**

By default, Simmate registers its core apps automatically. You can see your active apps under the `apps` key of your settings. If you've previously removed apps and want to restore the defaults, you can reset your `~/simmate/settings.yaml` or manually add them back using `simmate config add`.

## View installed apps

To see which apps are currently registered with your Simmate installation, run:

``` bash
simmate config show
```

In the output, your installed app configs are listed under the `apps` key:

``` bash
# example output
apps:
- simmate.apps.configs.AflowConfig
- simmate.apps.configs.BaderConfig
- simmate.apps.configs.BcpcConfig
- simmate.apps.configs.CodConfig
- simmate.apps.configs.EvolutionConfig
- simmate.apps.configs.InventoryManagementConfig
- simmate.apps.configs.JarvisConfig
- simmate.apps.configs.MaterialsProjectConfig
- simmate.apps.configs.OqmdConfig
- simmate.apps.configs.PriceCatalogConfig
- simmate.apps.configs.ProjectManagementConfig
- simmate.apps.configs.QuantumEspressoConfig
- simmate.apps.configs.VaspConfig
```

## Uninstall an app

!!! warning
    Removing an app from your settings does **not** remove its tables from your database.

To uninstall an app, go to your `~/simmate/settings.yaml` file and remove the target config(s) from the `apps:` list.


## Accessing tables

:material-arrow-left::material-arrow-left::material-arrow-left: Refer to [our database guide](/full_guides/database/basic_use.md) in the sidebar for in-depth usage.

All of an app's tables and datasets are packaged within its `models` module (e.g., `simmate.apps.example.models`). Simmate uses the [Django ORM](https://docs.djangoproject.com/en/5.1/topics/db/queries/), where a `model` represents a single database table.

!!! example
    To load the Materials Project structures table:

    ``` python
    from simmate.apps.materials_project.models import MatprojStructure
    ```

## Accessing workflows

:material-arrow-left::material-arrow-left::material-arrow-left: Refer to [our workflows guide](/full_guides/workflows/basic_use.md) in the sidebar for in-depth usage.

Advanced users can import a workflow class directly rather than using the `get_workflow` utility. All of an app's workflows are packaged within its `workflows` module.

!!! example
    `static-energy.vasp.mat-proj` is converted to `StaticEnergy__Vasp__MatProj` following [our workflow naming conventions](/full_guides/workflows/naming_conventions.md). You can import it from:

    ``` python
    from simmate.apps.materials_project.workflows import StaticEnergy__Vasp__MatProj
    ```
