
# Switching to a remote cluster

!!! warning
    This section can be extremely difficult for beginners. If you can, try to sit down with an experienced user or someone from your IT department as you work through it. Don't get discouraged if this section takes your more than an hour -- it's a lot to learn!

Thus far, you've been running Simmate on your local desktop or laptop, but we saw in the previous section, that we actually need VASP (which needs to be on Linux) for Simmate's workflows to run. 99% of the time, you'll be using a University or Federal supercomputer (aka "high performance computing (HPC) clusters"), which will have VASP already installed.

----------------------------------------------------------------------

## Cluster-specific guides

For teams that are actively using Simmate, we have extra notes and examples below on submitting to that particular cluster. This includes:

- **WarWulf**: The Warren lab's "BeoWulf" cluster at UNC Chapel Hill
- **LongLeaf**: UNC's university cluster most use-cases (1 node limit)
- **DogWood**: UNC's university cluster built for massively parallel jobs (>1 node)

!!! tip 
    If your cluster/university is not listed, contact your IT team for help in completing this tutorial.

----------------------------------------------------------------------

## A check-list for clusters

For workflows to run correctly, the following requirements need to be met:

- [x] a VASP license for your team ([purchased on their site](https://www.vasp.at/))
- [x] a remote cluster that you have a profile with (e.g. UNC's [LongLeaf](https://its.unc.edu/research-computing/longleaf-cluster/))
- [x] VASP installed on the remote cluster
- [x] Anaconda installed on the remote cluster

Make sure you have these steps completed before starting below

!!! tip
    For the Warren Lab, these items are configured for you already on `WarWulf`,
    `LongLeaf`, and `DogWood`.

----------------------------------------------------------------------

## 1. Sign in to the cluster

If you've never signed into a remote cluster before, we will do this by using SSH (Secure Shell).

Run the following command in your local terminal:

=== "example"
    ``` shell
    ssh my_username@my_cluster.edu
    ```
=== "WarWulf"
    ``` shell
    ssh WarrenLab@warwulf.net
    ```
    !!! note
        everyone shares the profile "WarrenLab". Ask Scott for the password (scw@email.unc.edu)
    
=== "LongLeaf"
    ``` shell
    ssh my_onyen@longleaf.unc.edu
    ```
=== "DogWood"
    ``` shell
    ssh my_username@my_cluster.edu
    ```

!!! danger
    on windows, use your Command-prompt -- not the Anaconda Powershell Prompt


After entering your password, you are now using a terminal on the remote supercomputer. Try running the command `pwd` ("print working directory") to show that your terminal is indeed running commands on the remote cluster, not your desktop:

``` shell
# This is the same for all linux clusters
pwd
```

----------------------------------------------------------------------

## 2. Load VASP

To load VASP into your environment, you typically need to run a 'load module' command:

=== "example"
    ``` shell
    module load vasp
    ```
=== "WarWulf"
    ``` shell
    module load vasp; source /opt/ohpc/pub/intel/bin/ifortvars.sh;
    ```
=== "LongLeaf"
    ``` shell
    module load vasp/5.4.4
    ```
=== "DogWood"
    ``` shell
    module load vasp/5.4.4
    ```

Then check that the vasp command is found. If the vasp_std command worked correctly, you will see the following output (bc their command doesn't print help information like `simmate` or `conda`):

``` shell
vasp_std
```

``` shell
# Error output may vary between different VASP versions
Error reading item 'VCAIMAGES' from file INCAR.
```

----------------------------------------------------------------------

## 3. Build your personal Simmate env

Next we need to ensure Simmate is installed. 

If you see `(base)` at the start of your command-line, Anaconda is already installed.

If not, ask your IT team how they want you install it. Typically it's by using [miniconda](https://docs.conda.io/en/latest/miniconda.html) which is just anaconda without the graphical user interface). 

With Anaconda set up, you can create your environment and install Simmate just like we did in the first tutorial:

``` shell
# Create your conda env with...

conda create -n my_env -c conda-forge python=3.10 simmate
conda activate my_env


# Initialize your database on this new installation.

simmate database reset
```

!!! danger
    On WarWulf, we share a profile so make sure you name your environment something
    unique. For example, use `yourname_env` (e.g. `jacks_env`).

----------------------------------------------------------------------

## 4. Set up VASP potentials

!!! note
    This step is already completed for you on the `WarWulf` cluster

Next, copy your Potentials into `~/simmate/vasp/Potentials` and also copy the `POSCAR` file above onto your cluster. 

It can be diffult in the command line to move files around or even transfer them back and forth from your local computer to the supercomputer. It's much easier with a program like [FileZilla](https://filezilla-project.org/), [MobaXTerm](https://mobaxterm.mobatek.net/), or another file transfer program. We recommend FileZilla, but it's entirely optional and up to you.

Review [our POTCAR guide](/getting_started/run_a_workflow/configure_potcars/) from before if you need help on this step.

----------------------------------------------------------------------

## 5. Move to your 'scratch' directory

Typically, clusters will have a "scratch" directory that you should submit jobs from -- which is different from your home directory. Make sure you switch to that before submitting and workflows. (note, your `POSCAR` and all input files should be in this directory too):

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

## 6. Build our input files

Just like we did on our laptop, we need to make our input files. For now,
let's use this sample YAML file:

``` yaml
workflow_name: static-energy.vasp.mit
structure:
    database_table: MatprojStructure
    database_id: mp-22862
command: mpirun -n 4 vasp_std > vasp.out  # OPTIONAL
directory: my_custom_folder  # OPTIONAL
```

Put this in a file named `my_settings.yaml` in your scratch directory.

!!! danger
    Take note of the `-n 4` in our command. This is the number of cores that
    we want our calculation to use. Make sure this number matches your 
    `cpus-per-task` setting in the next section

----------------------------------------------------------------------

## 7. Build our submit script

Earlier in this tutorial, we called `simmate workflows run ...` directly in our terminal, but this should **NEVER** be done on a supercomputer. Instead we should submit the workflow to the cluster's job queue. Typically, supercomputers use SLURM or PBS to submit jobs.

For example, UNC's `WarWulf`, `LongLeaf`, and `DogWood` clusters each use [SLURM](https://slurm.schedmd.com/documentation.html). 

To submit, we would make a file named `submit.sh`:

``` shell
nano submit.sh
```

... and use contents likes ...


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

    #. /opt/ohpc/pub/suppress.sh  #supress infiniband output, set vasp path

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
        Note the massive `ntasks` and `node` values here. DogWood is only meant for
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

----------------------------------------------------------------------

## 8. Double check everything 

Let's go back through our check list before we submit 

- [x] loaded the VASP module
- [x] activated your conda environment
- [x] in the temporary working directory
- [x] have our `yaml` file (+ extra inputs like a POSCAR) in the directory
- [x] have our `submit.sh` in the directory
- [x] structure file (e.g. `POSCAR`) is present in working directory

If all of these are set, you're good to go.

----------------------------------------------------------------------

## 9. Submit a workflow to the queue

Finally, let's submit to our cluster! :fire::fire::fire::rocket:

``` shell
sbatch submit.sh
```

----------------------------------------------------------------------

## 10. Monitor its progress

You can then monitor your jobs progress with:

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

## Success!

You've now submitted a Simmate workflow to a remote cluster :partying_face: :partying_face: :partying_face: !!! 

!!! tip
    Be sure to go back through this section a few times before moving on. Submitting remote jobs can be tedious but it's important to understand. Advanced features of Simmate will let you skip a lot of this work down the road, but that won't happen until we reaching the "Adding Computational Resources" guide.

----------------------------------------------------------------------
