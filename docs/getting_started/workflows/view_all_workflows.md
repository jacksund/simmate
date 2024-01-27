# Exploring Available Workflows

----------------------------------------------------------------------

## Accessing All Workflows

Simmate can be used to compute a material's energy, structure, or properties. For each of these needs, we have preconfigured workflows. You can access all of these via the `simmate workflows` command.

To view all available workflows, run:

``` shell
simmate workflows list-all
```

The output will resemble the following:

```
These are the workflows that have been registered:
        (01) customized.vasp.user-config
        (02) diffusion.vasp.neb-all-paths-mit
        (03) diffusion.vasp.neb-from-endpoints-mit
        (04) diffusion.vasp.neb-from-images-mit
        (05) diffusion.vasp.neb-single-path-mit
        (06) dynamics.vasp.matproj
        (07) dynamics.vasp.mit
        (08) dynamics.vasp.mvl-npt
        (09) electronic-structure.vasp.matproj-full
  ... << additional workflows truncated for brevity >>
```

!!! note
    All workflows are named using the format `{type}.{app}.{preset}`:

    1. `type`: The type of property/analysis
    2. `app`: The program(s) used in the workflow
    3. `preset`: The name of settings/preset used

----------------------------------------------------------------------

## Understanding a Workflow

Next, use the `explore` command for a more interactive way to view the available workflows.

``` shell
simmate workflows explore
```

When prompted, select a workflow type or a specific preset. A description of the chosen workflow will be displayed at the end.

For example, here's the output of the `relaxation.vasp.staged` workflow, frequently used in our evolutionary search algorithm. This output was obtained by running `simmate workflows explore`, selecting `relaxation`, then `vasp`, and then `staged`:

```
===================== relaxation.vasp.staged =====================


Description:

Runs a series of increasing-quality relaxations and then finishes with a single static energy calculation.

This workflow is most useful for randomly-created structures or extremely large supercells. More precise relaxations+energy calcs should be done
afterwards because ettings are still below MIT and Materials Project quality.


Parameters:

REQUIRED PARAMETERS
--------------------
- structure

OPTIONAL PARAMETERS (+ their defaults):
---------------------------------------
- command: null
- source: null
- directory: null
- run_id: null
- compress_output: false

*** 'null' indicates the parameter is set with advanced logic

To understand each parameter, you can read through our parameter docs, which give full descriptions and examples.


==================================================================
```

----------------------------------------------------------------------

## Understanding Parameters

In the above message, there's a reference to our **Parameter docs**. You can access this
page by clicking the **Parameters** section at the top of this webpage (or click [here](/simmate/parameters)).

This page provides a comprehensive list of ALL parameters for ALL workflows. If you want to learn more about a specific input, this is your go-to resource.

----------------------------------------------------------------------

## Choosing a Workflow for Practice

For the remainder of this tutorial, we will use the `static-energy.quantum-espresso.quality00` workflow, which performs a basic static energy calculation.

Take a look at this workflow using `simmate workflows explore` before moving on.

----------------------------------------------------------------------
