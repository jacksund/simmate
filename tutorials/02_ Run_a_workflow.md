# Run a workflow

In this tutorial, you will use the command line to view all available workflows and their settings. Beginners will also be introduced to remote terminals (SSH) and jobs queue (such as SLURM).

1. [The quick tutorial](#the-quick-tutorial)
2. [The full tutorial](#the-full-tutorial)
    - [The 4 stages of a workflow](#the-4-stages-of-a-workflow)
    - [Configuring Potentials (for VASP users)](#configuring-potentials-for-vasp-users)
    - [Setting up our database](#setting-up-our-database)
    - [Making a structure file for practice](#making-a-structure-file-for-practice)
    - [Viewing available workflows](#viewing-available-workflows)
    - [Viewing a workflow's settings and inputs](#viewing-a-workflows-settings-and-inputs)
    - [Finally running your workflow!](#finally-running-our-workflow)
    - [Switching to a remote cluster](#switching-to-a-remote-cluster)

<br/><br/>

# The quick tutorial

> :warning: for the quick tutorial, we assume you have VASP installed and that the `vasp_std` command is in the available path. In the future, we hope to update this tutorial with a workflow that doesn't require VASP or remote Linux cluster. Until then, we apologize for the inconvenience. :cry:

1. Before running a workflow, we must initialize our Simmate database with `simmate database reset`. Your database will be built at `~/simmate/database.sqlite3`.
2. To practice calculating, make structure file for tablesalt (NaCl). Name it `POSCAR`, where the contents are...
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
3. View a list of all workflows available with `simmate workflows list-all`
4. View the settings used for the `energy_mit` workflow with `simmate workflows show-config energy_mit`
5. Copy and paste VASP POTCAR files to the folder `~/simmate/vasp/Potentials`. Be sure to unpack the `tar.gz` files. This folder will have the potentials that came with VASP -- and with their original folder+file names:
```
# Located at /home/my_username (~)
simmate/
└── vasp
    └── Potentials
        ├── LDA
        │   ├── potpaw_LDA
        │   ├── potpaw_LDA.52
        │   ├── potpaw_LDA.54
        │   └── potUSPP_LDA
        ├── PBE
        │   ├── potpaw_PBE
        │   ├── potpaw_PBE.52
        │   └── potpaw_PBE.54
        └── PW91
            ├── potpaw_GGA
            └── potUSPP_GGA
```
6. View the input files with `simmate workflows setup-only energy_mit POSCAR`
7. Run a workflow with `simmate workflows run energy_mit POSCAR` (run = configure + schedule + execute + save). This command should be submitted via a SLURM/PBS job script on HPC clusters.
8. For now, you can manually go through the files to see the results. We will cover how to access your database in a later tutorial (05).

<br/><br/>

# The full tutorial

> :bulb: You will start this tutorial on your local computer, even if you don't have VASP installed. By the end of the tutorial, you will have switched to a computer with VASP (likely a remote university or federal supercomputer).

<br/> <!-- add empty line -->

## The 4 stages of a workflow

Before running any workflows, it is important to understand what's happening behind the scenes. All workflows carry out four steps:

- `configure`: chooses our desired settings for the calculation (such as VASP's INCAR settings)
- `schedule`: decides whether to run the workflow immediately or send off to a job queue (e.g. SLURM, PBS, or remote computers)
- `execute`: writes our input files, runs the calculation (e.g. VASP), and checks the results for errors
- `save`: saves the results to our database

There are many different scenarios where we may want to change the behavior of these steps. For example, what if I want to `execute` on a remote computer instead of my local one? Or if I want to `save` results to a cloud database that my entire lab shares? These can be configured easily, but because they require extra setup, we will save them for a later tutorial.

For now, we just want to run a workflow using Simmate's default settings. Without setting anything up, here is what Simmate will do:

- `configure`: take the default settings from the workflow you request
- `schedule`: decides that we want to run the workflow immediately
- `execute`: runs the calculation directly on our local computer
- `save`: saves the results on our local computer

Before we can actually run this workflow, we must:

1. tell Simmate where our VASP files are
2. set up our database so results can be saved
3. select a structure for our calculation

The next three sections will address each of these requirements.

<br/> <!-- add empty line -->

## Setting up our database

We often want to run the same calculation on many materials, so Simmate pre-builds database tables for us to fill. This just means we make tables (like those used in Excel), where we have all the column headers ready to go. For example, you can imagine that a table of structures would have columns for formula, density, and number of sites, among other things. Simmate builds these tables for you and automatically fills all the columns with data after a calculation finishes. We will explore what these tables look like in tutorial 5, but for now, we want Simmate to create them. All we have to do is run the following command 

```
simmate database reset
```

When you call this command, Simmate will print out a bunch of information -- this can be ignored for now. It's just making all of your tables.

> :warning: Every time you run the command `simmate database reset`, the database is deleted and a new one is written with empty tables.  If you want to keep your previous runs, you should save a copy of your database. If you share a home directory with other users, check with them before running this command.

So where is the database stored? After running `simmate database reset`, you'll find it in a file named `~/simmate/database.sqlite3`. To find this file:
1. remember from tutorial 1 that `~` is short for our home directory -- typically something like `/home/jacksund/` or `C:\Users\jacksund`.
2. have "show hidden files" turned on in your File Explorer (on Windows, check "show file name extensions" under the "View" tab). Then you'll see a file named `database.sqlite3` instead of just `database`.

You won't be able to double-click this file. Just like how you need Excel to open and read Excel (.xlsx) files, we need a separate program to read database (.sqlite3) files. We'll use Simmate to do this later on.

But just after that one command, our database is setup any ready to use! We can now run workflows and start adding data to it.

<br/> <!-- add empty line -->

## Making a structure file

Before we run a workflow, we need a crystal structure to run it on. There are many ways to get a crystal structure -- such as downloading one online or using a program to create one from scratch. Here, in order to learn about structure files, we are going to make one from scratch without any program.

First, make a new text file on your Desktop named `POSCAR.txt`. You can use which text editor you prefer (Notepad, Sublime, etc.). You can also create the file using the command like with:

```
nano POSCAR.txt
```

Note, we can see the `.txt` ending because we enabled "show file name extensions" above.

Once you have this file, copy/paste this text into it:

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

This text is everything we need to represent a structure, which is just a lattice and a list of atomic sites. The lattice is defined by a 3x3 matrix (lines 3-5) and the sites are just a list of xyz coordinates with an element (lines 8-9 show fractional coordinates). There are many different ways to write this information; here we are using the VASP's POSCAR format. Another popular format is CIF. It's not as clean and tidy as a POSCAR, but it holds similar information:
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

Nearly all files that you will interact with are text files -- just in different formats. That's where file extensions come in. They indicate what format we are using. Files named `something.cif` just tell programs we have a text file written if the CIF structure format. VASP uses the name POSCAR (without any file extension) to show its format. So rename your file from `POSCAR.txt` to `POSCAR`, and now all programs (VESTA, OVITO, and others) will know what to do with your structure. In Windows, you will often receive a warning about changing the file extension. Ignore the warning and change the extension.

If you're using the command-line to create/edit this file, you can use the copy (`cp`) command to make the `POSCAR` file:

```
cp POSCAR.txt POSCAR
```

> :bulb: **fun fact**: a Microsoft Word document is just a folder of text files. The .docx file ending tells Word that we have the folder in their desired format. Try renaming a word file from `my_file.docx` to `my_file.zip` and open it up to explore. Nearly all programs do something like this!

We now have our structure ready to go! Let's get back to running a workflow.

<br/> <!-- add empty line -->

## Configuring Potentials (for VASP users)

> :warning: once Simmate switches from VASP to a free DFT alternative, this section of the tutorial will be removed. 

VASP is a very popular software for running DFT calculations, but our team can't install it for you because VASP is commercially licensed (i.e. you need to [purchase it from their team](https://www.vasp.at/), which we are not affiliated with). Simmate is working to switch to another DFT software -- specifically one that is free/open-source, that can be preinstalled for you, and that you can use on Windows+Mac+Linux. Until Simmate reaches this milestone, you'll have to use VASP. We apologize for the inconvenience.

While VASP can only be installed on Linux, we will still practice configuring VASP with Simmate on our local computer. To do this, you only need the Potentials that are distrubited with the VASP installation files. You can either...

1. Grab these from the VASP installation files. You can find them at `vasp/5.x.x/dist/Potentials`. Be sure to unpack the `tar.gz` files.
2. Ask a team member or your IT team for a copy of these files.

Once you have the potentials, paste them into a folder named `~/simmate/vasp/Potentials`. Note, this is same directory that your database is in (`~/simmate`) where you need to make a new folder named `vasp`. This folder will have the potentials that came with VASP -- and with their original folder+file names. Once you have all of this done, you're folder should look like this:

```
# Located at /home/my_username (~)
simmate/
├── database.sqlite3
└── vasp
    └── Potentials
        ├── LDA
        │   ├── potpaw_LDA
        │   ├── potpaw_LDA.52
        │   ├── potpaw_LDA.54
        │   └── potUSPP_LDA
        ├── PBE
        │   ├── potpaw_PBE
        │   ├── potpaw_PBE.52
        │   └── potpaw_PBE.54
        └── PW91
            ├── potpaw_GGA
            └── potUSPP_GGA
```

If you made this folder incorrectly, commands that you use later will fail with an error like...

```python
FileNotFoundError: [Errno 2] No such file or directory: '/home/jacksund/simmate/vasp/Potentials/PBE/potpaw_PBE.54/Na/POTCAR'
```

If you see this error, double-check your folder setup.

> :warning: our team only has access to VASP v5.4.4, so if your folder structure differs for newer versions of VASP, please let our know by [opening an issue](https://github.com/jacksund/simmate/issues).


<br/> <!-- add empty line -->

## Viewing available workflows

At the most basic level, you'll want to use Simmate to calculate a material's energy, structure, or properties. For each type of task, we have prebuilt workflows. All of these are accessible through the `simmate workflows` command.

Let's start by seeing what is available by running:

```
simmate workflows list-all
```

The output will be similar to...

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

In this tutorial, we will be using `energy_mit` which runs a simple static energy calculation using MIT Project settings (these settings are based on pymatgen's [MITRelaxSet](https://pymatgen.org/pymatgen.io.vasp.sets.html#pymatgen.io.vasp.sets.MITRelaxSet)).

<br/> <!-- add empty line -->

## Viewing a workflow's settings and inputs

Take a look back at the 4 key steps of a workflow above (`configure`, `schedule`, `execute`, and `save`). Here, we will inspect the `configure` step.

To view a workflow's configuration before using it, we type the command `simmate workflows show-config`. Try this out by running:

```
simmate workflows show-config relaxation_quality00
```

VASP users will recognize that this specifies the contents of a VASP INCAR file.  The `relaxation_quality00` is the most basic workflow configuration because the INCAR will not depend on the structure or composition of your crystal.

Next, look at a more advanced calculation. Run the command:

```
simmate workflows show-config energy_mit
```

Here, you'll see that some INCAR settings rely on composition and that we have a list of error handlers to help ensure that the calculation finishes successfully.

Now, let's go one step further and provide a specific structure (the POSCAR we just made) into a specific workflow (energy_mit). To do this, make sure our terminal has the same folder open as where our file is! For example, if your POSCAR is on your Desktop while your terminal is in your home directory, you can type `cd Desktop` to change your active folder to your Desktop. Then run the command:

```
simmate workflows setup-only energy_mit POSCAR
```

You'll see a new folder created named `MIT_Static_Energy_inputs`. When you open it, you'll see all the files that Simmate made for VASP to use. This is useful when you're an advanced user who wants to alter these files before running VASP manually -- this could happen when you want to test new workflows or unique systems.

For absolute beginners, you don't immediately need to understand these files, but they will eventually be important for understanding the scientific limitations of your results or for running your own custom calculations. Whether you use [VASP](https://www.vasp.at/wiki/index.php/Category:Tutorials), [ABINIT](https://docs.abinit.org/tutorial/), or another program, be sure to go through their tutorials, rather than always depending on Simmate to run the program for you.  Until you reach that point, we'll have Simmate do it all for us!

<br/> <!-- add empty line -->

## Finally running our workflow!

> :warning: Unless you have VASP installed on your local computer, these next commands will fail. **That is okay!** Let's go ahead and try running these commands anyways. It will be helpful to see how Simmate workflows fail when VASP is not configured properly. If you don't have VASP installed, you'll see an error stating that the `vasp_std` command isn't known (such as `vasp_std: not found` on Linux). We'll switch to a remote computer with VASP installed in the next section.

The default Simmate settings will run everything immediately and locally on your desktop. When running the workflow, it will create a new folder, write the inputs in it, run the calculation, and save the results to your database.

The command to do this with our POSCAR and energy_mit workflow is: 

```
simmate workflows run energy_mit POSCAR
```

By default, Simmate uses the command `vasp_std > vasp.out` and creates a new `simmate-task` folder with a unique identifier (ex: `simmate-task-j8djk3mn8`).

What if we wanted to change this command or the directory it's ran in? First, check the help output for the command:
```
simmate workflows run --help
```

Using this help info, we can change our folder name (`--directory`, `-d`) as well as the command used to run VASP (`--command`, `-c`). For example, we can update our command to this:

```
simmate workflows run energy_mit POSCAR -c "mpirun -n 4 vasp_std > vasp.out" -d my_custom_folder
```


If any errors come up, please let our team know by [posting a question](https://github.com/jacksund/simmate/discussions/categories/q-a). If not, congrats :partying_face: :partying_face: :partying_face: !!! You now know how to run workflows with a single command and understand what Simmate is doing behind the scenes.

<br/> <!-- add empty line -->

## Switching to a remote cluster

> :warning: This section can be extremely difficult for beginners. If you can, try to sit down with an experienced user or someone from your IT department as you work through it. Don't get discouraged if this section takes your more than an hour -- it's a lot to learn!

Thus far, you've been running Simmate on your local desktop or laptop, but we saw in the previous section, that we actually need VASP (which needs to be on Linux) for Simmate's workflows to run. 99% of the time, you'll be using a University or Federal supercomputer (aka "high performance computing (HPC) clusters"), which will have VASP already installed.

For teams that are actively using Simmate, we have a guides on submitting to that particular cluster. [Check to see if your university or federal cluster is listed](#). Use these guides as you work through the rest of this section. If your cluster/university is not listed, contact your IT team for help in completing this tutorial.

For workflows to run correctly, the following requirements need to be met:

1. a VASP license for your team ([purchased on their site](https://www.vasp.at/))
2. a remote cluster that you have a profile with (e.g. UNC's [LongLeaf](https://its.unc.edu/research-computing/longleaf-cluster/))
3. VASP installed on the remote cluster
4. Anaconda installed on the remote cluster
5. Simmate installed on the remote cluster
6. VASP Potentials in `~/simmate/vasp/Potentials` on the remote cluster

The remainder of this tutorial gives example commands to use. Replace these commands and scripts with the ones in your cluster's guide.

If you've never signed into a remote cluster before, we will do this by using SSH (Secure Shell). For example, to sign in to University of North Carolina's LongLeaf cluster, you would run the following command in your local terminal (on windows, use your Command-prompt -- not the Anaconda Powershell Prompt):

```
ssh my_username@longleaf.unc.edu
```

After entering your password, you are now using a terminal on the remote supercomputer. Try running the command `pwd` ("print working directory") to show that your terminal is indeed running commands on the remote cluster, not your desktop:

```
pwd
```

To load VASP into your environment, you typically need to run the command:

```
module load vasp
vasp_std
```

If the vasp_std command worked correctly, you will see (their command doesn't print help information like `simmate` or `conda`):

```
Error reading item 'VCAIMAGES' from file INCAR.
```

Next we need to ensure Simmate is installed. If you see `(base)` at the start of your command-line, Anaconda is already installed! If not, ask your IT team how they want you install it (typically it's by using [miniconda](https://docs.conda.io/en/latest/miniconda.html) which is just anaconda without the graphical user interface). With Anaconda set up, you can create your environment and install Simmate just like we did in tutorial 01:

```
conda create -n my_env -c conda-forge python=3.8 simmate
conda activate my_env

# Initialize your database on this new installation.
# If you share a username with others, check your guide before running this.
simmate database reset
```

Lastly, copy your Potentials into `~/simmate/vasp/Potentials` and also copy the `POSCAR` file above on your cluster. It can be diffult in the command line to move files around or even transfer them back and forth from your local computer to the supercomputer. It's much easier with a program like [FileZilla](https://filezilla-project.org/), [MobaXTerm](https://mobaxterm.mobatek.net/), or another file transfer window. We recommend FileZilla, but it's entirely optional and up to you.

Finally, let's submit a Simmate workflow on our cluster! In the previous section, we called `simmate workflows run ...` directly in our terminal, but this should **NEVER** be done on a supercomputer. Instead we should submit the workflow to the cluster's job queue. Typically, supercomputers use SLURM or PBS to submit jobs.

For example, UNC's longleaf cluster uses [SLURM](https://slurm.schedmd.com/documentation.html). To submit, we would make a file named `submit.sh` with the contents:

```
#! /bin/sh

#SBATCH --job-name=my_example_job
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=4GB
#SBATCH --time=01:00:00
#SBATCH --partition=general
#SBATCH --output=slurm.out 
#SBATCH --mail-type=ALL 
#SBATCH --mail-user=my_username@live.unc.edu

simmate workflows run energy_mit POSCAR
```

Make sure you have VASP and your correct conda enviornment loaded. Then submit your job with:

```
sbatch submit.sh
```

You've now submitted a Simmate workflow to a remote cluster :partying_face: :partying_face: :partying_face: !!! 

Be sure to go back through this tutorial a few times before moving on. Submitting remote jobs can be tedious but it's important to understand. Advanced features of Simmate will let you skip a lot of this work down the road, but that won't happen until tutorial 07.

When you're ready, you can advance to [the next tutorial](https://github.com/jacksund/simmate/blob/main/tutorials/03_Analyze_and_modify_structures.md), which be back on your local computer.
