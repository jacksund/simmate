# Switching to a Remote Cluster

!!! warning
    This section may be challenging for beginners. If possible, work through it with an experienced user or someone from your IT department. Don't be discouraged if it takes more than an hour -- there's a lot to learn!

!!! tip
    Moving files around or transferring them between your local computer and the supercomputer can be challenging in the command line. It's much easier with a program like [FileZilla](https://filezilla-project.org/), [MobaXTerm](https://mobaxterm.mobatek.net/), or another file transfer program. We recommend MobaXTerm, but it's entirely optional and up to you.

----------------------------------------------------------------------

## Overview

Up until now, you've been running Simmate on your local desktop or laptop. However, as we saw in the previous sections, we need a DFT software (which often requires Linux) for Simmate's workflows to run. Most of the time, you'll be using a University or Federal supercomputer (also known as "high performance computing (HPC) clusters"), which will already have some of this software (VASP, QE, etc.) installed.

### Cluster-Specific Guides

For teams actively using Simmate, we provide additional notes and examples for submitting to specific clusters. This includes:

- **WarWulf**: The Warren lab's "BeoWulf" cluster at UNC Chapel Hill
- **LongLeaf**: UNC's university cluster for most use-cases (1 node limit)
- **DogWood**: UNC's university cluster designed for massively parallel jobs (>1 node)

!!! tip 
    If your cluster/university is not listed, contact your IT team for assistance in completing this tutorial.

### Prerequisites

For workflows to run correctly, the following requirements must be met:

- [x] A remote cluster that you have a profile with (e.g., UNC's [LongLeaf](https://its.unc.edu/research-computing/longleaf-cluster/))
- [x] Anaconda installed on the remote cluster
- [x] QE installed on the remote cluster

Ensure these steps are completed before proceeding.

!!! tip
    For the Warren Lab, these items are already configured on `WarWulf`,
    `LongLeaf`, and `DogWood`.

----------------------------------------------------------------------

## 1. Sign in to the Cluster

If you've never signed into a remote cluster before, we will do this using SSH (Secure Shell). Run the following command in your local terminal:

=== "example"
    ``` shell
    ssh my_username@my_cluster.edu
    ```
=== "WarWulf"
    ``` shell
    ssh WarrenLab@warwulf.net
    ```
    !!! note
        Everyone shares the profile "WarrenLab". Ask Scott for the password (scw@email.unc.edu)
    
=== "LongLeaf"
    ``` shell
    ssh my_onyen@longleaf.unc.edu
    ```
=== "DogWood"
    ``` shell
    ssh my_username@my_cluster.edu
    ```

!!! danger
    On Windows, use your Command Prompt -- not the Anaconda Powershell Prompt.

After entering your password, you are now using a terminal on the remote supercomputer. Try running the command `pwd` ("print working directory") to show that your terminal is indeed running commands on the remote cluster, not your desktop:

``` shell
# This is the same for all Linux clusters
pwd
```

----------------------------------------------------------------------

## 2. Build Your Personal Simmate Environment

Next, we need to ensure Simmate is installed. 

If you see `(base)` at the start of your command line, Anaconda is already installed.

If not, ask your IT team how they want you to install it. Typically, it's by using [miniconda](https://docs.conda.io/en/latest/miniconda.html), which is just Anaconda without the graphical user interface. 

With Anaconda set up, you can create your environment and install Simmate just like we did in the first tutorial:

``` shell
# Create your conda environment with...

conda create -n my_env -c conda-forge python=3.11 simmate
conda activate my_env

# Initialize your database on this new installation.
simmate database reset
```

!!! danger
    On WarWulf, we share a profile, so make sure you name your environment something
    unique. For example, use `yourname_env` (e.g., `jacks_env`).

----------------------------------------------------------------------

## 3. Load & Configure QE

To load QE into your environment, you typically need to run a 'load module' command:

=== "example"
    ``` shell
    module load qe
    ```
=== "WarWulf"
    ``` shell
    module load qe
    ```
=== "LongLeaf"
    ``` shell
    module load qe
    ```
=== "DogWood"
    ``` shell
    module load qe
    ```

Then check that the `pw.x` command is found and QE configured correctly:

``` bash
simmate-qe test
```

If the potentials are missing, you have Simmate download and configure them:

``` bash
simmate-qe setup sssp
```

----------------------------------------------------------------------

## 4. Move to Your 'Scratch' Directory

Typically, clusters have a "scratch" directory that you should submit jobs from -- which is different from your home directory. Make sure you switch to that before submitting any workflows. Your `POSCAR` and all input files should be in this directory too:

=== "example"
    ``` shell
    cd /path/to/my/scratch/space/
    ```
=== "WarWulf"
    ``` shell
    cd /media/synology/user/your_name
    ```
=== "LongLeaf"
    ``` shell
    cd /pine/scr/j/a/jacksund
    ```
=== "DogWood"
    ``` shell
    cd /21dayscratch/scr/y/o/youronyen
    ```

----------------------------------------------------------------------

## 5. Build Our Input Files

Just like we did on our laptop, we need to make our input files. For now,
let's use this sample YAML file:

``` yaml
workflow_name: static-energy.quantum-espresso.quality00
# instead of POSCAR, we will use MatProj
structure:
    database_table: MatprojStructure
    database_id: mp-22862
command: mpirun -n 4 pw.x < pwscf.in > pw-scf.out  # OPTIONAL
directory: my_custom_folder  # OPTIONAL
```

Put this in a file named `my_settings.yaml` in your scratch directory.

!!! danger
    Take note of the `-n 4` in our command. This is the number of cores that
    we want our calculation to use in parallel. Make sure this number matches your 
    `cpus-per-task` setting in the next section.

----------------------------------------------------------------------

## 6. Build Our Submit Script

Earlier in this tutorial, we called `simmate workflows run ...` directly in our terminal, but this should **NEVER** be done on a supercomputer. Instead, we should submit the workflow to the cluster's job queue. Typically, supercomputers use SLURM or PBS to submit jobs.

For example, UNC's `WarWulf`, `LongLeaf`, and `DogWood` clusters each use [SLURM](https://slurm.schedmd.com/documentation.html). 

To submit, we would make a file named `submit.sh`:

``` shell
nano submit.sh
```

... and use contents like ...


=== "example"
    ``` slurm
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

    simmate workflows run my_settings.yaml
    ```
=== "WarWulf"
    ``` slurm
    #!/bin/bash

    #. /opt/ohpc/pub/suppress.sh  #suppress infiniband output, set vasp path

    #SBATCH --job-name=my_example_job
    #SBATCH --nodes=1
    #SBATCH --ntasks=1
    #SBATCH --cpus-per-task=4
    #SBATCH --mem=4GB
    #SBATCH --time=01:00:00
    #SBATCH --partition=p1
    #SBATCH --output=slurm.out 
    #SBATCH --mail-type=ALL 
    #SBATCH --mail-user=my_username@live.unc.edu

    simmate workflows run my_settings.yaml
    ```
=== "LongLeaf"
    ``` slurm
    #! /bin/sh

    #SBATCH --job-name=my_example_job
    #SBATCH --nodes=20
    #SBATCH --ntasks=1
    #SBATCH --mem=40g
    #SBATCH --partition=general
    #SBATCH --output=slurm.out
    #SBATCH --mail-type=FAIL
    #SBATCH --mail-user=youronyen@live.unc.edu
    #SBATCH --time=11-00:00

    simmate workflows run my_settings.yaml
    ```
=== "DogWood"
    !!! danger
        Note the large `ntasks` and `node` values here. DogWood is only meant for
        large calculations, so talk with our team before submitting.
    ``` slurm
    #!/bin/sh

    #SBATCH --job-name=NEB
    #SBATCH --ntasks=704
    #SBATCH --nodes=16
    #SBATCH --time=2-00:00
    #SBATCH --mem=300g
    #SBATCH --partition=2112_queue
    #SBATCH --mail-type=ALL
    #SBATCH --mail-user=lamcrae@live.unc.edu

    simmate workflows run my_settings.yaml
    ```

!!! info
    Each of these `SBATCH` parameters sets how we would like to submit a job and how many resources we expect to use. These are explained in [SLURM's documentation for sbatch](https://slurm.schedmd.com/sbatch.html), but you may need help from your IT team to update them. But to break down these example parameters...
    
    - `job-name`: the name that identifies your job. It will be visible when you check the status of your job.
    - `nodes`: the number of server nodes (or CPUs) that you request. Typically leave this at 1.
    - `ntasks`: the number tasks that you'll be running. We run one workflow at a time here, so we use 1.
    - `cpus-per-task`: the number of CPU tasks required for each run. We run our workflow using 4 cores (`mpirun -n 4`), so we need to request 4 cores for it here.
    - `mem`: the memory requested for this job. If it is exceeded, the job will be terminated.
    - `time`: the maximum time requested for this job. If it is exceeded, the job will be terminated.
    - `partition`: the group of nodes that we request resources on. You can often remove this line and use the cluster's default.
    - `output`: the name of the file to write the job output (including errors).
    - `mail-type` + `mail-user`: will send an email alerts when a jobs starts/stops/fails/etc.

----------------------------------------------------------------------

## 7. Double Check Everything 

Let's go back through our checklist before we submit:

- [x] Loaded the Quantum Espresso module
- [x] Activated your conda environment
- [x] In the temporary working directory
- [x] Have our `yaml` file (+ extra inputs like a POSCAR) in the directory
- [x] Have our `submit.sh` in the directory
- [x] Structure file (e.g., `POSCAR`) is present in working directory

If all of these are set, you're good to go.

----------------------------------------------------------------------

## 8. Submit a Workflow to the Queue

Finally, let's submit to our cluster! :fire::fire::fire::rocket:

``` shell
sbatch submit.sh
```

----------------------------------------------------------------------

## 9. Monitor Its Progress

You can then monitor your job's progress with:

=== "example"
    ``` shell
    squeue -u my_username
    ```
=== "WarWulf"
    ``` shell
    sq
    # or
    sq | grep my_name
    ```
    !!! example
        `sq | grep jack`
    
=== "LongLeaf"
    ``` shell
    squeue -u my_onyen
    ```
=== "DogWood"
    ``` shell
    squeue -u my_onyen
    ```

----------------------------------------------------------------------

## 10. Success!

Congratulations! You've now submitted a Simmate workflow to a remote cluster :partying_face: :partying_face: :partying_face: !!! 

!!! tip
    Be sure to review this section a few times before moving on. Submitting remote jobs can be tedious, but it's important to understand. Advanced features of Simmate will let you skip a lot of this work down the road, but that won't happen until we reach the "Adding Computational Resources" guide.

----------------------------------------------------------------------