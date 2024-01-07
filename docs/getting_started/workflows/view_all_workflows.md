# Exploring Available Workflows

----------------------------------------------------------------------

## Recap

In the preceding sections, we accomplished the following prerequisites for running a workflow:

- [x] Specified the location of our VASP files to Simmate
- [x] Configured our database for result storage
- [x] Selected a structure for our calculation

Now, let's delve into the various workflows at our disposal and select one to execute.

----------------------------------------------------------------------

## Accessing All Workflows

Primarily, Simmate is used to compute a material's energy, structure, or properties. For each of these tasks, we have preconfigured workflows. You can access all of these via the `simmate workflows` command.

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

----------------------------------------------------------------------

## Understanding a Workflow

Next, use the `explore` command for a more interactive way to view the available workflows.

``` shell
simmate workflows explore
```

When prompted, select a workflow type or a specific preset. A description of the chosen workflow will be displayed at the end. For instance, here's the output of the `relaxation.vasp.staged` workflow, frequently used in our evolutionary search algorithm. This output was obtained by running `simmate workflows explore`, selecting option `6` (relaxation), and then option `1` (matproj):

```
===================== relaxation.vasp.matproj =====================


Description:

This task is a reimplementation of pymatgen's MPRelaxSet.                                                                                                                       

Runs a VASP geometry optimization using Materials Project settings.                                                                                                             

Materials Project settings are often considered the minimum-required quality for publication and is sufficient for most applications. If you are looking at one structure in    
detail (for electronic, vibrational, and other properties), you should still test for convergence using higher-quality settings.                                                


Parameters:

REQUIRED PARAMETERS
--------------------
- structure

OPTIONAL PARAMETERS (+ their defaults):
---------------------------------------
- directory: null
- command: vasp_std > vasp.out
- is_restart: false
- run_id: null
- compress_output: false
- source: null
- standardize_structure: false
- symmetry_precision: 0.01
- angle_tolerance: 0.5

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

For the remainder of this tutorial, we will use the `static-energy.vasp.mit` workflow, which performs a basic static energy calculation using MIT Project settings (these settings are based on pymatgen's [MITRelaxSet](https://pymatgen.org/pymatgen.io.vasp.sets.html#pymatgen.io.vasp.sets.MITRelaxSet)).

----------------------------------------------------------------------