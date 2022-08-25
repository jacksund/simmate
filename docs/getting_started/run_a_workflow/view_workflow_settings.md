
# Viewing a workflow's settings and inputs

Take a look back at the 4 key steps of a workflow above (`configure`, `schedule`, `execute`, and `save`). Here, we will inspect the `configure` step.

To view a workflow's configuration before using it, we type the command `simmate workflows show-config`. Try this out by running:

``` shell
simmate workflows show-config relaxation.vasp.quality00
```

VASP users will recognize that this specifies the contents of a VASP INCAR file.  The `quality00` is the most basic workflow configuration because the INCAR will not depend on the structure or composition of your crystal.

Next, look at a more advanced calculation. Run the command:

``` shell
simmate workflows show-config static-energy.vasp.mit
```

Here, you'll see that some INCAR settings rely on composition and that we have a list of error handlers to help ensure that the calculation finishes successfully.

Now, let's go one step further and provide a specific structure (the POSCAR we just made) into a specific workflow (static-energy/mit). To do this, make sure our terminal has the same folder open as where our file is! For example, if your POSCAR is on your Desktop while your terminal is in your home directory, you can type `cd Desktop` to change your active folder to your Desktop. Then run the command:

``` shell
simmate workflows setup-only static-energy.vasp.mit --structure POSCAR
```

You'll see a new folder created named `static-energy.vasp.mit.SETUP-ONLY`. When you open it, you'll see all the files that Simmate made for VASP to use. This is useful when you're an advanced user who wants to alter these files before running VASP manually -- this could happen when you want to test new workflows or unique systems.

For absolute beginners, you don't immediately need to understand these files, but they will eventually be important for understanding the scientific limitations of your results or for running your own custom calculations. Whether you use [VASP](https://www.vasp.at/wiki/index.php/Category:Tutorials), [ABINIT](https://docs.abinit.org/tutorial/), or another program, be sure to go through their tutorials, rather than always depending on Simmate to run the program for you.  Until you reach that point, we'll have Simmate do it all for us!
