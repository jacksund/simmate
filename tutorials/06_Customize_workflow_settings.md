# Customize Workflow Settings

In this tutorial, you will learn how to add custom settings into your workflows. We'll also explore why custom-setting results are stored separately from default-setting results.

1. [The quick tutorial](#the-quick-tutorial)
2. [The full tutorial](#the-full-tutorial)
    - [Customization is for testing. New Workflows are for production.](#customization-is-for-testing-new-workflows-are-for-production)
    - [How to run a workflow with custom settings](#how-to-run-a-workflow-with-custom-settings)
    - [Where results from custom settings are stored](#where-results-from-custom-settings-are-stored)
    - [How to add machine-specific settings to ALL workflows](#how-to-add-machine-specific-settings-to-all-workflows)

> :warning: we assume you have VASP installed and that the `vasp` command is in the available path. In the future, we hope to update this tutorial with a workflow that doesn't require any extra installations. Until then, we apologize for the inconvenience. :cry:

<br/><br/>

# The quick tutorial

1. We intentially avoid the use of `workflow.run(custom_settings=...)`. **This will NOT work.** Customization is strictly for testing, and results will be stored to a separate database table. If you would like to customize a workflow and apply it to many systems/structures, you should instead move to tutorial 9.
2. To run a workflow with custom settings, we use the `run_custom` method instead of `run`.
```python
from simmate.workflows.all import energy_mit

# This is how we ran workflows before
results = energy_mit.run(structure=nacl_structure)

# This is how we run using custom settings
results = energy_mit.run_custom(
    structure=nacl_structure, 
    custom_settings={"ENCUT": 500},
)
```



# The full tutorial
