
# Viewing all available workflows

----------------------------------------------------------------------

## Review

In the last three sections, we completed our check list for running a workflow:

- [x] tell Simmate where our VASP files are
- [x] set up our database so results can be saved
- [x] select a structure for our calculation

Now we can explore the different workflows available and choose one to run.

----------------------------------------------------------------------

## Viewing all workflows

At the most basic level, you'll want to use Simmate to calculate a material's energy, structure, or properties. For each type of task, we have prebuilt workflows. All of these are accessible through the `simmate workflows` command.

Let's start by seeing what is available by running:

``` shell
simmate workflows list-all
```

The output will be similar to...

```
These are the workflows that have been registerd:
        (01) customized.vasp.user-config
        (02) diffusion.vasp.neb-all-paths-mit
        (03) diffusion.vasp.neb-from-endpoints-mit
        (04) diffusion.vasp.neb-from-images-mit
        (05) diffusion.vasp.neb-single-path-mit
        (06) dynamics.vasp.matproj
        (07) dynamics.vasp.mit
        (08) dynamics.vasp.mvl-npt
        (09) electronic-structure.vasp.matproj-full
  ... << plus others that are cut-off for clarity >>
```

----------------------------------------------------------------------

## Learning about a workflow

Next, try out the `explore` command, which gives us a more interactive way to view the available workflows.

``` shell
simmate workflows explore
```

When prompted to choose a type of workflow or a specific preset, choose whichever you'd like! A description of the workflow will be printed at the very end. As an example, here's the output of an example workflow `relaxation.vasp.staged` which is commonly used in our evolutionary search algorithm. To get this output, we used the `simmate workflows explore` then selected option `6` (relaxation) and then option `1` (matproj):

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

## Learning about parameters

In the message above, there's a link to our **Parameter docs**. You can access this
page by clicking the **Parameters** section at the top of this webpage (or click [here](/simmate/parameters)).

This page lists out ALL parameters for ALL workflows. If there's an input you'd
like to learn more above -- this is the place to start.

----------------------------------------------------------------------

## Selecting our practice workflow

In the rest of tutorial, we will be using `static-energy.vasp.mit` which runs a simple static energy calculation using MIT Project settings (these settings are based on pymatgen's [MITRelaxSet](https://pymatgen.org/pymatgen.io.vasp.sets.html#pymatgen.io.vasp.sets.MITRelaxSet)).

----------------------------------------------------------------------
