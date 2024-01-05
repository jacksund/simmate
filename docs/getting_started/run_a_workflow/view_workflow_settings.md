# Accessing Workflow Settings and Inputs

!!! warning
    This section is designed for seasoned VASP users who wish to preview settings. Beginners may not frequently use the commands provided here.

----------------------------------------------------------------------

## Accessing Basic Settings

To preview a workflow's configuration prior to its use, enter the command `simmate workflows show-config`. Test this by executing:

``` shell
simmate workflows show-config relaxation.vasp.quality00
```

VASP users will recognize this as specifying the contents of a VASP INCAR file. The `quality00` represents the most fundamental workflow configuration as the INCAR will not be influenced by the structure or composition of your crystal.

----------------------------------------------------------------------

## Accessing Complex Settings

Next, examine a more sophisticated calculation. Execute the command:

``` shell
simmate workflows show-config static-energy.vasp.mit
```

Here, you'll observe that some INCAR settings are dependent on composition and that we have a list of error handlers to ensure the successful completion of the calculation.

----------------------------------------------------------------------

## Generating Input Files (Optional)

Now, let's advance further and input a specific structure (the POSCAR we just created) into a specific workflow (static-energy/mit). To do this, ensure that our terminal is open in the same folder as our file! For instance, if your POSCAR is on your Desktop while your terminal is in your home directory, you can type `cd Desktop` to switch your active folder to your Desktop. Then execute the command:

``` shell
simmate workflows setup-only static-energy.vasp.mit --structure POSCAR
```

You'll notice a new folder named `static-energy.vasp.mit.SETUP-ONLY`. Upon opening it, you'll find all the files that Simmate created for VASP to utilize. This is beneficial for advanced users who wish to modify these files prior to manually running VASP -- this could occur when you want to experiment with new workflows or unique systems.

!!! note
    For absolute beginners, understanding these files is not immediately necessary, but they will eventually become crucial for comprehending the scientific limitations of your results or for executing your own custom calculations. Whether you use [VASP](https://www.vasp.at/wiki/index.php/Category:Tutorials), [ABINIT](https://docs.abinit.org/tutorial/), or another program, it's recommended to go through their tutorials, rather than solely relying on Simmate to run the program for you. Until you reach that stage, we'll let Simmate handle everything.

----------------------------------------------------------------------