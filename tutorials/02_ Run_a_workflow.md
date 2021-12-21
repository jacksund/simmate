# Setting up your database, running your first workflow, and viewing the results

> :warning: we assume you have VASP installed and that the `vasp` command is in the available path. In the future, we hope to update this tutorial with a workflow that doesn't require any extra installations. Until then, we apologize for the inconvenience. :cry: (note: maybe do something like an XRD?)

# The quick version

2. View a list of all workflows available with `simmate workflows list-all`
4. See the settings used for the `relaxation_mit` with `simmate workflows show-config relaxation_mit`
3. To practice calculating, make structure file for tablesalt (NaCl). Name it `POSCAR`, where the contents are...
```
Na1 Cl1
1.0
3.485437 0.000000 2.012318
1.161812 3.286101 2.012318
0.000000 0.000000 4.024635
Na Cl
1 1
direct
0.000000 0.000000 0.000000 Na
0.500000 0.500000 0.500000 Cl
```

5. View the input files with `simmate workflows setup-only relaxation_mit POSCAR` _**(optional)**_
6. Before running any workflows, we must initialize our Simmate database with `simmate databate reset` 
7. Run a workflow with `simmate workflows run relaxation_mit POSCAR` (run = set up + execute + save to db)
8. Start the simmate test server with `simmate run-server`
9. You can now view the web UI at http://127.0.0.1:8000/
10. In the web UI, navigate to `calculations` --> `relaxations` --> `EMT` to view our results

# The full tutorial

## Viewing available workflows

At the most basic level, you'll want to use Simmate to calculate a structure's energy, band structure, or some other characteristic. For that, we have prebuilt workflows that you can run using simple commands. All of these are accessible through the `simmate workflows` command.

Let's start by seeing what is available by running `simmate workflows list-all`. You should see something like:

```
Gathering all available workflows...
These are all workflows you can use:
	(1) energy_mit
	(2) energy_quality04
	(3) relaxation_mit
	(4) relaxation_quality00
	(5) relaxation_quality01
	(6) relaxation_quality02
	(7) relaxation_quality03
	(8) relaxation_quality04
	(9) relaxation_staged
  ... << plus others that are cut-off for clarity >>
```

In this tutorial, we will be using `relaxation_mit` which runs a simple static energy calculation using MIT Project settings (these settings are based off of pymatgen's [MITRelaxSet](https://pymatgen.org/pymatgen.io.vasp.sets.html#pymatgen.io.vasp.sets.MITRelaxSet)). Before we run this, we should understand

## The basic components of a workflow

Before running any of these workflows, it is important to understand what's happening behind the scenes. The simplest workflows involve just a single calculation (such as an energy calculation), and when we `run` a workflow, there are the four steps all workflows go through:

- `configure`: chooses our desired settings for the calculation (such as VASP's INCAR settings)
- `schedule`: decides whether to run the workflow immediately or send off to a job queue (e.g. SLURM, PBS, or remote computers)
- `execute`: writes our input files, runs the calculation (e.g. calling VASP), and checks the results for errors
- `save`: saves the results to our database

There are many different scenarios where we may want to change the behavior of these steps. For example, what if I want to run the workflow on some remote computer instead of my local one? Or if I want to save results to a cloud database that my entire lab shares? These can be configured easily, but we are going to save that for a later tutorial. 

For now, we just want to run a workflow using Simmate's default settings. Without setting anything up, here is what Simmate will do:

- `configure`: take the default settings from the workflow you request
- `schedule`: decides we want to run the workflow immediately
- `execute`: runs the calculation directly on our local computer
- `save`: saves the results on our local computer

We are going to keep these default settings for now. Tutorials 7 and 8 will teach you how to edit this bevahior -- and these are advanced tutorials.

Before we can actually run these different stages of a workflow, the next two sections will help us address two things:

1. set up our database tables
2. make an input structure

## Setting up our database

We often want to run the same exact calculation on many materials, so Simmate pre-builds database tables for us to fill. This just means we make tables (just like those used in Excel), where we have all the column headers ready to go. For example, you can imagine a table of structures would have columns like formula, density, number of sites, etc.. Simmate builds these tables for you and automatically fills all the columns with data after a calculation is ran. We will explore what these datatables look like in tutorial 4, but for now, we just want to run our first workflow.

Before we can fill a table with data, we need the table to exist first! All we have to do is run the command `simmate database reset` to do this. When you call this command, Simmate will print out a bunch of information -- this can be ignored for now. It's just making all of your tables.

After running the command `simmate database reset`, let's go see where the tables were written. You'll find them in a file named `~/.simmate/database.sqlite3`. However, finding this may be tricky for beginners *(note, if you struggle here, you can simply move on to the next step. don't worry.)*. Here are some tips to help you:
1. remember from tutorial 1 that `~` is our home directory -- typically something like `/home/jacksund/` or `C:\Users\jacksund`. 
2. the period in `.simmate` means that the folder is hidden (it won't show up in your file viewer even though it's really there), so make sure in your File Explorer that you have "show Hidden Files" selected (on Windows, check "Hidden Items" under the "View" tab). 
3. we want to get in the habbit of viewing file extensions, so make sure you have "show file name extensions" enabled too. Then you'll see a file named `database.sqlite3` instead of just`database`.

Every time you run the command `simmate database reset`, this file is deleted and a new one is written with empty tables.

You won't be able to double-click this file. Just like how you need Excel to open and read Excel (.xlsx) files, we need some program to read database (.sqlite3) files. We'll use Simmate to do this later on.

But just after that one command, our database is setup any ready! We can now run workflows and start adding data to it.

## Making a structure file to test

Before we run a workflow, we need a crystal structure to run it on. There are many ways to get a crystal structure -- such as downloading one online or using a program to create one from scratch. Here, in order to learn about structure files, we are going to make one from scratch without any program.

First, make a new text file on your Desktop named `POSCAR.txt`. Note, we can see the `.txt` ending because we enabled "show file name extensions" above. Once you have this file, past this text into it:

```
Na1 Cl1
1.0
3.485437 0.000000 2.012318
1.161812 3.286101 2.012318
0.000000 0.000000 4.024635
Na Cl
1 1
direct
0.000000 0.000000 0.000000 Na
0.500000 0.500000 0.500000 Cl
```

This text is everything we need to represent a structure, which is just a lattice and a list of atomic sites. The lattice is defined by a 3x3 matrix (at the top of our file) and the sites are just a list of xyz coordinates with an element (shown at the bottom as fractional coordinates). There are many different ways to write this information, where here we are using the VASP format (aka the POSCAR format). Another popular format is CIF, which organizes the same data in a different format. It's not as clean and tidy as the VASP format, but its the exact same information:
```
data_NaCl
_symmetry_space_group_name_H-M   'P 1'
_cell_length_a   4.02463542
_cell_length_b   4.02463542
_cell_length_c   4.02463542
_cell_angle_alpha   60.00000000
_cell_angle_beta   60.00000000
_cell_angle_gamma   60.00000000
_symmetry_Int_Tables_number   1
_chemical_formula_structural   NaCl
_chemical_formula_sum   'Na1 Cl1'
_cell_volume   46.09614833
_cell_formula_units_Z   1
loop_
 _symmetry_equiv_pos_site_id
 _symmetry_equiv_pos_as_xyz
  1  'x, y, z'
loop_
 _atom_site_type_symbol
 _atom_site_label
 _atom_site_symmetry_multiplicity
 _atom_site_fract_x
 _atom_site_fract_y
 _atom_site_fract_z
 _atom_site_occupancy
  Na  Na0  1  0.00000000  0.00000000  0.00000000  1
  Cl  Cl1  1  0.50000000  0.50000000  0.50000000  1
```

Nearly all files that you will interact with are text files -- just in different formats. That's where file extensions come in. They indicate what format we are using. Files named `something.cif` just tell programs we have a text file written if the CIF structure format. VASP uses the name POSCAR (no file extension) to show it's format. So rename you file from `POSCAR.txt` to `POSCAR`, and now all programs (VESTA, OVITO, and others) will know what to do with your structure.

> :bulb: **fun fact**: a Microsoft Word document is just a folder of text files. The .docx file ending tells Word that we have the folder in their desired format. Try renaming your a word file from `my_file.docx` to `my_file.zip` and open it up to explore. Nearly all programs do something like this!

We now have our structure ready to go! Let's get back to running our workflow.

## Viewing the workflow settings and inputs

Take a look back at the 4 key steps of a workflow above. Here, we will inspect a workflow to see how it `configures` it's settings.

You'll often want to see what settings a workflow uses before actually running it. To do this, we can use the `simmate workflows show-config` command. Try this out by running `simmate workflows show-config relaxation_quality00`. VASP users will recognize this as a very simple calculation where it's just printing out settings passed into the INCAR file. These are the most basic settings because the INCAR will be the same for all structures, regardless of their composition.

Now let's look at an advanced calculation, which picks settings based off of composition and also checks for (then fixes) common errors. Run the command `simmate workflows show-config relaxation_mit`. Here, you'll see some INCAR settings rely on composition and we have a list of error handlers to help ensure a calculation completes.

So we can now view the settings used for *all* compositions/structures, but now we want to give it a specific structure. We'll give it the POSCAR structure we just made. To do this, make sure our terminal has the same folder open as where our file is! For example, if your POSCAR is on your Desktop while your terminal is in your home directory, you can run `cd Desktop` to change your active folder to your Desktop. Then run the command `simmate workflows setup-only relaxation_mit POSCAR`. You'll see a new folder created named `relaxation_mit_input`. When you open it, these are all of the files that Simmate made for VASP to use. This is useful when you're an advanced user that wants to alter these files before calling VASP manually -- this happens often when testing out new workflows or unique systems.

For absolute beginners, you don't need to need to immediately understand these files/settings, but they will be important for knowing the scientific limitations of your results and for running your own custom calculations. For whichever program you end up using the most, be sure to also go through their tutorials -- rather than always using Simmate to run their program for you. Here, we're using VASP where you can learn to use VASP independently with [their tutorials](https://www.vasp.at/wiki/index.php/Category:Tutorials). Until you reach that point, we'll have Simmate do it all for us!

## Finally running our workflow!

Recall from above that the default Simmate settings run everything immediately and locally on your desktop. When running the workflow, it will create a new folder, write the inputs in it, run the calculation, and then save the results to your database.

The command to do this with our POSCAR and relaxation_mit workflow is `simmate workflows run relaxation_mit POSCAR`. By default, Simmate uses the command `vasp > vasp.out` and creates a ran folder name (ex: `simmate-task-j8djk3mn8`) for this to run in.

Alternatively, we can change the command used to call VASP as well as the directory we want this ran in. All of the options are given in `simmate workflows run --help`. For the command and directory, we can update our command to look something like this:
```
simmate workflows run relaxation_mit POSCAR -c "mpirun -n 4 vasp > vasp.out" -d my_folder
```

If any errors come up, please let our team know by [posting a question](https://github.com/jacksund/simmate/discussions/new?category=q-a).

If not, congrats :partying_face: :partying_face: :partying_face: !!! You now know how to run workflows with a single command and understand what Simmate is doing behind the scenes.

## Viewing results

> :warning: The website interface isn't ready yet, so you'll have to manually go through the files to see the results. You can still move on to the other tutorials, which will show you how to see the results with python as well.
