# Run a workflow

In this tutorial, you will use the command line to view all available workflows and their settings. Beginners will also be introduced to remote terminals (SSH) and jobs queue (such as SLURM).

1. [The quick tutorial](#the-quick-tutorial)
2. [The full tutorial](#the-full-tutorial)
    - [The 4 stages of a workflow](#the-4-stages-of-a-workflow)
    - [Setting up our database](#setting-up-our-database)
    - [Making a structure file for practice](#making-a-structure-file-for-practice)
    - [Viewing available workflows](#viewing-available-workflows)
    - [Viewing a workflow's settings and inputs](#viewing-a-workflows-settings-and-inputs)
    - [Finally running your workflow!](#finally-running-our-workflow)
    - [Switching to a remote cluster](#switching-to-a-remote-cluster)

<br/><br/>

# The quick tutorial

> :warning: we assume you have VASP installed and that the `vasp_std` command is in the available path. In the future, we hope to update this tutorial with a workflow that doesn't require VASP. Until then, we apologize for the inconvenience. :cry:

1. Before running a workflow, we must initialize our Simmate database with `simmate database reset`. Your database will be built at `~/.simmate/database.sqlite3`.
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
5. Copy and paste VASP POTCAR files to the folder `~/.simmate/vasp/Potentials`. This folder will have the potentials that came with VASP -- and with their original folder+file names. For example there would be an LDA folder that contains subfolders potpaw_LDA, potpaw_LDA.52, potpaw_LDA.54, and so on. Make sure these folders aren't compressed (no *.zip files).
6. View the input files with `simmate workflows setup-only energy_mit POSCAR`
7. Run a workflow with `simmate workflows run energy_mit POSCAR` (run = configure + schedule + execute + save)
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

1. set up our database so results can be saved
2. select a structure for our calculation

<br/> <!-- add empty line -->

## Setting up our database

We often want to run the same calculation on many materials, so Simmate pre-builds database tables for us to fill. This just means we make tables (like those used in Excel), where we have all the column headers ready to go. For example, you can imagine that a table of structures would have columns for formula, density, and number of sites, among other things. Simmate builds these tables for you and automatically fills all the columns with data after a calculation finishes. We will explore what these tables look like in tutorial 5, but for now, we want Simmate to create them. All we have to do is run the command `simmate database reset` to do this. When you call this command, Simmate will print out a bunch of information -- this can be ignored for now. It's just making all of your tables.

> :warning: Every time you run the command `simmate database reset`, the database is deleted and a new one is written with empty tables.  If you want to keep your previous runs, you should save a copy of your database. If you share a home directory with other users, check with them before running this command.

So where is the database stored? After running `simmate database reset`, you'll find it in a file named `~/.simmate/database.sqlite3`. However, finding this may be tricky for beginners *(Note, if you struggle here, you can simply move on to the next section. Don't worry.)*. Here are some tips to help you:
1. remember from tutorial 1 that `~` is short for our home directory -- typically something like `/home/jacksund/` or `C:\Users\jacksund`. 
2. the period in `.simmate` means that the simmate folder is hidden. It won't show up in your file viewer unless you have "show hidden files" turned on in your File Explorer (on Windows, check "Hidden Items" under the "View" tab). 
3. we want to get in the habit of viewing file extensions, so make sure you also have "show file name extensions" enabled. Then you'll see a file named `database.sqlite3` instead of just `database`.

You won't be able to double-click this file. Just like how you need Excel to open and read Excel (.xlsx) files, we need a separate program to read database (.sqlite3) files. We'll use Simmate to do this later on.

But just after that one command, our database is setup any ready to use! We can now run workflows and start adding data to it.

<br/> <!-- add empty line -->

## Making a structure file

Before we run a workflow, we need a crystal structure to run it on. There are many ways to get a crystal structure -- such as downloading one online or using a program to create one from scratch. Here, in order to learn about structure files, we are going to make one from scratch without any program.

First, make a new text file on your Desktop named `POSCAR.txt`. Note, we can see the `.txt` ending because we enabled "show file name extensions" above. Once you have this file, copy/paste this text into it:

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

Nearly all files that you will interact with are text files -- just in different formats. That's where file extensions come in. They indicate what format we are using. Files named `something.cif` just tell programs we have a text file written if the CIF structure format. VASP uses the name POSCAR (without any file extension) to show its format. So rename your file from `POSCAR.txt` to `POSCAR`, and now all programs (VESTA, OVITO, and others) will know what to do with your structure. In Windows, you will often receive a warning about changing the file extension.  Ignore the warning and change the extension.

> :bulb: **fun fact**: a Microsoft Word document is just a folder of text files. The .docx file ending tells Word that we have the folder in their desired format. Try renaming a word file from `my_file.docx` to `my_file.zip` and open it up to explore. Nearly all programs do something like this!

We now have our structure ready to go! Let's get back to running a workflow.

<br/> <!-- add empty line -->

## Viewing available workflows

At the most basic level, you'll want to use Simmate to calculate a material's energy, structure, or properties. For each type of task, we have prebuilt workflows. All of these are accessible through the `simmate workflows` command.

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

In this tutorial, we will be using `energy_mit` which runs a simple static energy calculation using MIT Project settings (these settings are based on pymatgen's [MITRelaxSet](https://pymatgen.org/pymatgen.io.vasp.sets.html#pymatgen.io.vasp.sets.MITRelaxSet)).

<br/> <!-- add empty line -->

## Viewing a workflow's settings and inputs

Take a look back at the 4 key steps of a workflow above (`configure`, `schedule`, `execute`, and `save`). Here, we will inspect the `configure` step.

To view a workflow's configuration before using it, we type the command `simmate workflows show-config`. Try this out by running `simmate workflows show-config relaxation_quality00`. VASP users will recognize that this specifies the contents of a VASP INCAR file.  The `relaxation_quality00` is the most basic workflow configuration because the INCAR will not depend on the structure or composition of your crystal.

Next, look at a more advanced calculation. Run the command `simmate workflows show-config energy_mit`. Here, you'll see that some INCAR settings rely on composition and that we have a list of error handlers to help ensure that the calculation finishes successfully.

> :warning: For this next step, you need to have VASP POTCARs available, which our team is not allowed to distribute. You can either (1) configure them now, or (2) skip to the next section (we will address the installation of VASP in the "Switching to a remote cluster" section below. 

> (from the section below) To "configure" POTCARs with Simmate, we need to only copy/paste them to the folder ~/.simmate/vasp/Potentials. This is where Simmate will look for them. This folder will have the potentials that came with VASP -- and with their original folder+file names. For example there would be an LDA folder that contains subfolders potpaw_LDA, potpaw_LDA.52, potpaw_LDA.54, and so on. Make sure these folders aren't compressed (so not *.zip files).

Now, let's go one step further and feed a specific structure (the POSCAR we just made) into a specific workflow (energy_MIT). To do this, make sure our terminal has the same folder open as where our file is! For example, if your POSCAR is on your Desktop while your terminal is in your home directory, you can type `cd Desktop` to change your active folder to your Desktop. Then run the command `simmate workflows setup-only energy_mit POSCAR`. You'll see a new folder created named `MIT_Static_Energy_inputs`. When you open it, you'll see all the files that Simmate made for VASP to use. This is useful when you're an advanced user who wants to alter these files before running VASP manually -- this could happen when you want to test new workflows or unique systems.

For absolute beginners, you don't immediately need to understand these files, but they will eventually be important for understanding the scientific limitations of your results or for running your own custom calculations. Whether you use [VASP](https://www.vasp.at/wiki/index.php/Category:Tutorials), [ABINIT](https://docs.abinit.org/tutorial/), or another program, be sure to go through their tutorials, rather than always depending on Simmate to run the program for you.  Until you reach that point, we'll have Simmate do it all for us!

<br/> <!-- add empty line -->

## Finally running our workflow!

The default Simmate settings will run everything immediately and locally on your desktop. When running the workflow, it will create a new folder, write the inputs in it, run the calculation, and save the results to your database.

> :warning: Unless you have both (1) your POTCARs configured and (2) VASP installed on your local computer, these next commands will fail. **That is okay!** Let's go ahead and try running these commands anyways. It will be helpful to see how Simmate workflows fail when VASP is not configured properly. If you didn't configure your POTCARs, you'll see an error that states `FileNotFoundError: [Errno 2] No such file or directory: '/example/path/to/POTCAR'`. If you don't have VASP installed, you'll see an error stating that the `vasp_std` command isn't known (such as `vasp: not found` on Linux). The next section will help you address these errors.

The command to do this with our POSCAR and energy_mit workflow is `simmate workflows run energy_mit POSCAR`. By default, Simmate uses the command `vasp_std > vasp.out` and creates a new `simmate-task` folder with a unique identifier (ex: `simmate-task-j8djk3mn8`).

Alternatively, we can change our folder name as well as the command used to run VASP. For example, we can update our command to this:
```
simmate workflows run energy_mit POSCAR -c "mpirun -n 4 vasp_std > vasp.out" -d my_custom_folder
```

To see all the options for running workflows, type `simmate workflows run --help`.  

If any errors come up, please let our team know by [posting a question](https://github.com/jacksund/simmate/discussions/new?category=q-a). If not, congrats :partying_face: :partying_face: :partying_face: !!! You now know how to run workflows with a single command and understand what Simmate is doing behind the scenes.

<br/> <!-- add empty line -->

## Switching to a remote cluster

> :warning: This section can be extremely difficult for beginners. If you can, try to sit down with an experienced user or someone from your IT department as you work through it. Don't get discouraged if this section takes your more than an hour -- it's a lot to learn!

Thus far, you've been running Simmate on your local desktop or laptop, but we saw in the two previous sections, that we actually need VASP (which needs to be on Linux) for Simmate's workflows to run. VASP is a very popular software for running DFT calculations, but our team can't install it for you because VASP is commercially licensed (i.e. you need to [buy it from their team](https://www.vasp.at/), which we are not affiliated with). Simmate is working to switch to another DFT software -- specifically one that is free/open-source, that can be preinstalled for you, and that you can use on Windows+Mac+Linux. Until Simmate reaches this milestone, you'll have to use VASP. We apologize for the inconvenience.

Once you have a VASP license, the next step is installing it somewhere -- likely a University or Federal supercomputer. Many of these supercomputers (aka "high performance computing (HPC) clusters") will have VASP already installed. Contact your IT team and they can get you started. For example, the University of North Carolina (where Simmate is developed) has the [LongLeaf](https://its.unc.edu/research-computing/longleaf-cluster/) cluster and has guides on making an account. 

Signing into a remote cluster is typically done through SSH. For example, to sign in to the LongLeaf cluster, you would run the following command in your local terminal (on windows, use your Command-prompt -- not the Anaconda Powershell Prompt):

```
ssh my_username@longleaf.unc.edu
```

After entering your password, you are now using a terminal on the remote supercomputer! Try running the command `pwd` ("print working directory") to show that your terminal is indeed running commands on the remote cluster, not your desktop.

To load VASP, you typically need to run the command `module load vasp` or even `module load vasp/5.4.4`. Now try the command `vasp_std`. If everything was installed correctly, you won't get the `vasp_std: command not found` anymore!  If that didn't work, check which modules you have available by typing `module avail`.

If you see `(base)` at the start of your command-line, Anaconda is already installed! If not, ask your IT team how they want you install it (typically it's by using [miniconda](https://docs.conda.io/en/latest/miniconda.html) which is just anaconda without the graphical user interface). With Anaconda set up, you can create your environment and install Simmate just like we did in tutorial 01:

```
conda create -n my_env -c conda-forge python=3.8 simmate
conda activate my_env

# also, don't forget to initialize your database on this new installation
simmate database reset
```

We now have Simmate and VASP installed. Next, we need to tell Simmate where the VASP POTCARs are located. If you're unsure where these files are, you can ask your IT team where VASP's installation files are. These installation files will include the POTCARs in the Potentials folder.

To "configure" POTCARs with Simmate, copy/paste the Potentials folder into the ~/.simmate/vasp/Potentials. This is where Simmate will look for them. This folder will have the potentials that came with VASP -- and with their original folder+file names. For example there would be an LDA folder that contains subfolders potpaw_LDA, potpaw_LDA.52, potpaw_LDA.54, and so on. Make sure these folders aren't compressed (so not *.zip files).

> :bulb: It can be diffult in the command line to move files around or even transfer them back and forth from your local computer to the supercomputer. It's much easier with a program like [FileZilla](https://filezilla-project.org/), [MobaXTerm](https://mobaxterm.mobatek.net/), or another file transfer window. We recommend FileZilla, but it's entirely optional and up to you.

You can check that POTCARs are configured properly with the command `simmate workflows setup-only energy_mit POSCAR` (using the POSCAR from earlier in this tutorial).

Next, let's submit a Simmate workflow on our cluster! In the previous section, we called `simmate workflows run ...` directly in our terminal, but this should **NEVER** be done on a supercomputer. Instead we should submit the workflow to the cluster's job queue. Typically, supercomputers use SLURM or PBS to submit jobs. 

> :warning: The examples below use SLURM. PBS has very similar commands and setup to what's shown, but talk with your IT team to get started.

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

Make sure you have VASP and your correct conda enviornment loaded. Then submit your job with `sbatch submit.sh`.

You've now submitted a Simmate workflow to a remote cluster :partying_face: :partying_face: :partying_face: !!! 

Be sure to go back through this tutorial a few times before moving on. Submitting remote jobs can be tedious but it's important to understand. Advanced features of Simmate will let you skip a lot of this work down the road, but that won't happen until tutorial 07.
