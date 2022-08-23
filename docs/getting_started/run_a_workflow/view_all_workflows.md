
# Viewing all available workflows

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

Next, try out the `explore` command, which gives us a more interactive way to view the available workflows.

``` shell
simmate workflows explore
```

When prompted to choose a type of workflow or a specific preset, choose whichever you'd like! A description of the workflow will be printed at the very end. As an example, here's the output of an example workflow `relaxation.vasp.staged` which is commonly used in our evolutionary search algorithm. To get this output, we used the `simmate workflows explore` then selected option `6` (relaxation) and then option `9` (staged):

```
===================== relaxation/staged =====================

Using:

        from simmate.workflows.relaxation import Relaxation__Vasp__Quality00 

You can find the source code for this workflow in the follwing module: 

        simmate.calculators.vasp.workflows.relaxation


Description:

Runs a very rough VASP geometry optimization with fixed lattice volume. Quality 00 indicates these are absolute lowest quality settings used 
in our available presets.                                                                                                                    

Typically, you'd only want to run this relaxation on structures that were randomly created (and thus likely very unreasonable). More precise 
relaxations should be done afterwards. Therefore, instead of using this calculation, we recommend only using the relaxation/staged workflow, 
which uses this calculation as a first step.                                                                                                 


Parameters:

- command
- compress_output
- copy_previous_directory
- directory
- run_id
- source
- structure

==================================================================
```

In this tutorial, we will be using `static-energy.vasp.mit` which runs a simple static energy calculation using MIT Project settings (these settings are based on pymatgen's [MITRelaxSet](https://pymatgen.org/pymatgen.io.vasp.sets.html#pymatgen.io.vasp.sets.MITRelaxSet)).
