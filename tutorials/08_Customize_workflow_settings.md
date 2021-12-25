# Customize Workflow Settings

> :warning: these features are highly experimental and may change significantly before our first stable release. 

In this tutorial, you will learn how to run a workflow with customized settings. We will do this with the underlying `S3Task` becuase we don't want custom-setting results to be stored alongside default-setting results.

1. [The quick tutorial](#the-quick-tutorial)
2. [The full tutorial](#the-full-tutorial)
    - [Customization is for testing. New workflows are for production.](#customization-is-for-testing-new-workflows-are-for-production)
    - [How to run a workflow with custom settings](#how-to-run-a-workflow-with-custom-settings)
    - [Where results from custom settings are stored](#where-results-from-custom-settings-are-stored)
    - [How to add machine-specific settings to ALL workflows](#how-to-add-machine-specific-settings-to-all-workflows)

> :warning: we assume you have VASP installed and that the `vasp` command is in the available path. In the future, we hope to update this tutorial with a workflow that doesn't require any extra installations. Until then, we apologize for the inconvenience. :cry:

<br/><br/>

# The quick tutorial

1. We intentionally avoid the use of `workflow.run(custom_settings=...)`. **This will NOT work.** This is because we do not want to store results from customized settings in the same table as default settings -- it complicates analysis of many structuers/systems and makes navigating results extremely difficult for beginners. Instead, Simmate encourages the creation of new workflows and result tables when you want to customize settings.
3. To run a workflow with custom settings, we use the `run_custom` method instead of `run`.
```python
from simmate.workflows.all import energy_mit

# This is how we ran workflows before
status = energy_mit.run(structure=nacl_structure)

# This is how we run using custom settings
status = energy_mit.run_custom(
    structure=nacl_structure, 
    custom_settings={"ENCUT": 500},
)
```
3. The `run_custom` method does NOT store results in the `workflow.result_table` but instead in the `workflow.custom_result_table`. 

<br/><br/>

# The full tutorial

<br/>

## Customization is for testing. New workflows are for production.

<br/>

## How to run a workflow with custom settings

<br/>

## Where results from custom settings are stored

<br/>

## How to add machine-specific settings to ALL workflows

