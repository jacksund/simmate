
# Updating settings for a workflow

!!! danger
    The methods described in this section are **generally considered bad practice**, but they are still useful for getting things started. After this section, we will cover to best way to update settings and create new workflows.

----------------------------------------------------------------------

## Why isn't there a `custom_settings` option?

We intentionally avoid the use of `workflow.run(custom_settings=...)`. **This will NOT work.** Simmate does this because we do not want to store results from customized settings in the same results table -- as this would (a) complicate analysis of many structures/systems and (b) make navigating results extremely difficult for beginners. 

For example, reducing the `ENCUT` or changing the dispersion correction of a VASP calculation makes it so energies cannot be compared between all materials in the table, and thus, features like calculated hull energies would become inaccruate.

Instead, Simmate encourages the creation of new workflows and result tables when you want to customize settings. This puts Simmate's emphasis on "scaling up" workflows (i.e. running a fixed workflow on thousands on materials) as opposed to "scaling out" workflows (i.e. a flexible workflow that changes on a structure-by-structure basis).

----------------------------------------------------------------------

## Update settings for an existing workflow

For very quick testing, it is still useful to customize a workflow's settings without having to create a new workflow altogether. There are two approaches you can take to edit your settings:

### **OPTION 1** 

Writing input files and manually submitting a separate program

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

Using the "customized" workflow for a calculator (e.g. `customized.vasp.user-config`)

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
    These approaches are only possible with single-calcultion workflows (i.e. "nested" workflows that call several workflows within them are not supported)

----------------------------------------------------------------------

## **Avoid these approaches if possible!** 

Both of options shown above are only suitable for customizing settings for a few calculations -- and also you lose some key Simmate features. If you are submitting many calculations (>20) and this process doesn't suit your needs, keep reading!

----------------------------------------------------------------------
