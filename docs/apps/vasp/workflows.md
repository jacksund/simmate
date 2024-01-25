## VASP Workflows

--------------------------------------------------------------------------------

## Available Workflows

!!! note
    Many more VASP workflows are available in the `materials_project` and `warren_lab` apps.

    Guides on how to submit these are in the `Getting Started` and `Full Guides` sections.

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

Instead of constructing these tasks from numerous lower-level functions, we simplify these classes into a single `VaspWorkflow` class for easier interaction.

--------------------------------------------------------------------------------
