
# Switching to a remote cluster

> :warning: This section can be extremely difficult for beginners. If you can, try to sit down with an experienced user or someone from your IT department as you work through it. Don't get discouraged if this section takes your more than an hour -- it's a lot to learn!

Thus far, you've been running Simmate on your local desktop or laptop, but we saw in the previous section, that we actually need VASP (which needs to be on Linux) for Simmate's workflows to run. 99% of the time, you'll be using a University or Federal supercomputer (aka "high performance computing (HPC) clusters"), which will have VASP already installed.

For teams that are actively using Simmate, we have a guides on submitting to that particular cluster. [Check to see if your university or federal cluster is listed](https://github.com/jacksund/simmate/tree/main/tutorials/Guides_for_HPC_clusters). Use these guides as you work through the rest of this section. If your cluster/university is not listed, contact your IT team for help in completing this tutorial.

For workflows to run correctly, the following requirements need to be met:

1. a VASP license for your team ([purchased on their site](https://www.vasp.at/))
2. a remote cluster that you have a profile with (e.g. UNC's [LongLeaf](https://its.unc.edu/research-computing/longleaf-cluster/))
3. VASP installed on the remote cluster
4. Anaconda installed on the remote cluster
5. Simmate installed on the remote cluster
6. VASP Potentials in `~/simmate/vasp/Potentials` on the remote cluster

The remainder of this tutorial gives example commands to use. Replace these commands and scripts with the ones in your cluster's guide. (For example, the next command titled "Sign in with...", you should use the "Sign in with..." section of your cluster's guide.)

If you've never signed into a remote cluster before, we will do this by using SSH (Secure Shell). For example, to sign in to University of North Carolina's LongLeaf cluster, you would run the following command in your local terminal (on windows, use your Command-prompt -- not the Anaconda Powershell Prompt):

``` shell
# Sign in with...

ssh my_username@longleaf.unc.edu
```

After entering your password, you are now using a terminal on the remote supercomputer. Try running the command `pwd` ("print working directory") to show that your terminal is indeed running commands on the remote cluster, not your desktop:

``` shell
# This is the same for all linux clusters

pwd
```

To load VASP into your environment, you typically need to run the command:

``` shell
# Load VASP with...

module load vasp

# then check the command is found

vasp_std
```

If the vasp_std command worked correctly, you will see the following output (bc their command doesn't print help information like `simmate` or `conda`):

``` shell
# Error output may vary between different VASP versions

Error reading item 'VCAIMAGES' from file INCAR.
```

Next we need to ensure Simmate is installed. If you see `(base)` at the start of your command-line, Anaconda is already installed! If not, ask your IT team how they want you install it (typically it's by using [miniconda](https://docs.conda.io/en/latest/miniconda.html) which is just anaconda without the graphical user interface). With Anaconda set up, you can create your environment and install Simmate just like we did in tutorial 01:

``` shell
# Create your conda env with...

conda create -n my_env -c conda-forge python=3.10 simmate
conda activate my_env


# Initialize your database on this new installation.

simmate database reset
```

Next, copy your Potentials into `~/simmate/vasp/Potentials` and also copy the `POSCAR` file above onto your cluster. It can be diffult in the command line to move files around or even transfer them back and forth from your local computer to the supercomputer. It's much easier with a program like [FileZilla](https://filezilla-project.org/), [MobaXTerm](https://mobaxterm.mobatek.net/), or another file transfer window. We recommend FileZilla, but it's entirely optional and up to you.

Typically, clusters will have a "scratch" directory that you should submit jobs from -- which is different from your home directory. Make sure you switch to that before submitting and workflows. (note, your `POSCAR` should be in this directory too). Here is what LongLeaf's looks like as an example:

``` shell
# Access scratch directory with...

cd /pine/scr/j/a/jacksund
```

Finally, let's submit a Simmate workflow on our cluster! In the previous section, we called `simmate workflows run ...` directly in our terminal, but this should **NEVER** be done on a supercomputer. Instead we should submit the workflow to the cluster's job queue. Typically, supercomputers use SLURM or PBS to submit jobs.

For example, UNC's longleaf cluster uses [SLURM](https://slurm.schedmd.com/documentation.html). To submit, we would make a file named `submit.sh`:

``` shell
# Create a SLURM script with...

nano submit.sh
```

... and use contents likes ...

``` shell
#! /bin/sh

#SBATCH --job-name=my_example_job
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=4GB
#SBATCH --time=01:00:00
#SBATCH --partition=general
#SBATCH --output=slurm.out 
#SBATCH --mail-type=ALL 
#SBATCH --mail-user=my_username@live.unc.edu

simmate workflows run static-energy.vasp.mit --structure POSCAR --command "mpirun -n 4 vasp_std > vasp.out"
```

Each of these `SBATCH` parameters set how we would like to sumbit a job and how many resources we expect to use. These are explained in [SLURM's documnetation for sbatch](https://slurm.schedmd.com/sbatch.html), but you may need help from your IT team to update them. But to break down these example parameters...

- `job-name`: the name that identifies your job. It will be visible when you check the status of your job
- `nodes`: the number of server nodes (or CPUs) that you request. Typically leave this at 1.
- `ntasks`: the number tasks that you'll be running. We run one workflow at a time here, so we use 1.
- `cpus-per-task`: the number of CPU tasks required for each run. We run our workflow using 4 cores (`mpirun -n 4`) so we need to request 4 cores for it here
- `mem`: the memory requested for this job. If it is exceeded, the job will be terminated.
- `time`: the maximum time requested for this job. If it is exceeded, the job will be terminated.
- `partition`: the group of nodes that we request resources on. You can often remove this line and use the cluster's default.
- `output`: the name of the file to write the job output (including errors)
- `mail-type` + `mail-user`: will send an email alerts when a jobs starts/stops/fails/etc.

Make sure you have VASP and your correct conda enviornment loaded. Then submit your job with:

``` shell
# Submit with...

sbatch submit.sh
```

You can then monitor your jobs progress with:

``` shell
# Monitor progress with...

squeue -u my_username
```

You've now submitted a Simmate workflow to a remote cluster :partying_face: :partying_face: :partying_face: !!! 

Be sure to go back through this section a few times before moving on. Submitting remote jobs can be tedious but it's important to understand. Advanced features of Simmate will let you skip a lot of this work down the road, but that won't happen until tutorial 07.
