# Modifying Workflow Settings

!!! danger
    The techniques outlined in this section are **generally not recommended**, but they can be useful for initial setup. Following this, we will discuss the optimal method for modifying settings and creating new workflows.

----------------------------------------------------------------------

## Why isn't there a `custom_settings` option?

We deliberately do not use `workflow.run(custom_settings=...)`. **This will NOT work.** Simmate takes this approach because we want to avoid storing results from custom settings in the same results table. This would (a) complicate the analysis of multiple structures/systems and (b) make navigating results extremely challenging for beginners. 

For instance, altering the `ENCUT` or changing the dispersion correction of a VASP calculation would prevent energy comparisons between all materials in the table, rendering features like calculated hull energies inaccurate.

Instead, Simmate promotes the creation of new workflows and result tables for custom settings. This emphasizes Simmate's focus on "scaling up" workflows (i.e., running a fixed workflow on thousands of materials) rather than "scaling out" workflows (i.e., a flexible workflow that changes on a structure-by-structure basis).

----------------------------------------------------------------------

## Modifying settings for an existing workflow

For quick testing, it can be useful to adjust a workflow's settings without creating a new workflow. There are two methods to edit your settings:

### **OPTION 1** 

Write input files and manually submit a separate program

``` bash
# This simply writes input files
simmate workflows setup-only static-energy.vasp.mit --structure POSCAR

# access your files in the new directory
cd static-energy.vasp.mit.SETUP-ONLY

# Customize input files as you see fit.
# For example, you may want to edit INCAR settings
nano INCAR

# You can then submit VASP manually. Note, this will not use
# simmate at all! So there is no error handling and no results
# will be saved to your database.
vasp_std > vasp.out
```

### **OPTION 2** 

Use the "customized" workflow for an app (e.g., `customized.vasp.user-config`)

``` yaml
# In a file named "my_example.yaml".

# Indicates we want to change the settings, using a specific workflow as a starting-point
workflow_name: customized.vasp.user-config
workflow_base: static-energy.vasp.mit

# "Updated settings" indicated that we are updating some class attribute. 
# These fundamentally change the settings of a workflow. 
# Currently, only updating dictionary-based attributes are supported
updated_settings:
    incar: 
        ENCUT: 600
        KPOINTS: 0.25
    potcar_mappings:
        Y: Y_sv

# Then the remaining inputs are the same as the base workflow
input_parameters:
    structure: POSCAR
    command: mpirun -n 5 vasp_std > vasp.out
```

``` bash
# Now run our workflow from the settings file above.
# Results will be stored in a separate table from the
# base workflow's results.
simmate workflows run-yaml my_example.yaml
```

!!! warning
    These methods are only applicable to single-calculation workflows (i.e., "nested" workflows that call several workflows within them are not supported)

----------------------------------------------------------------------

## **Avoid these methods if possible!** 

Both options above are only suitable for customizing settings for a few calculations, and you lose some key Simmate features. If you are submitting many calculations (>20) and these methods do not meet your needs, continue reading!

----------------------------------------------------------------------