# Dogwood

Dogwood is a Linux-based computing system available for free to researchers across UNC Chapel Hill's campus. This cluster provides an environment that is optimized for large, multi-node workloads. There are different partitions useful for various types of jobs, and you can read more about the partition configurations ([here](https://its.unc.edu/research-computing/techdocs/dogwood-partitions-and-user-limits/)).  

> :bulb: This guide should be used alongside tutorial 02 ([here](https://github.com/jacksund/simmate/blob/main/tutorials/02_%20Run_a_workflow.md#switching-to-a-remote-cluster)).
<br/>

# The Simmate checklist

From the posted requirements:

1. a VASP license for your team **(COMPLETED)**
2. a remote cluster that you have a profile with 
3. VASP installed on the remote cluster **(COMPLETED)**
4. Anaconda installed on the remote cluster **(COMPLETED)**
5. Simmate installed on the remote cluster
6. VASP Potentials in `~/simmate/vasp/Potentials` on the remote cluster. Feel free to reach out with Scott with questions (scw@email.unc.edu)

For the uncompleted requirements:

2. you must create a profile on dogwood with your onyen. Directions for this are located [here](https://its.unc.edu/research-computing/longleaf-cluster/).
5. make your personal environment named `yourname_env` (e.g. `jacks_env`)
6. follow tutorial 02 ([here](https://github.com/jacksund/simmate/blob/main/tutorials/02_%20Run_a_workflow.md#configuring-potentials-for-vasp-users)) to set up VASP potentials

<br/>

# Example commands and scripts

Substitute these commands with the ones you see in the main tutorial.

<br/>

## Sign in with...
``` shell
ssh youronyen@dogwood.unc.edu
```

<br/>

## Load VASP with...
``` shell
module vasp/5.4.4
```

<br/>

## Call VASP with... 
Note, we use 704 cores here but update this to match your submit script
``` shell
mpirun -n 704 vasp_std > vasp.out
```

<br/>

## Create your conda env with...
``` shell
conda create -n my_env -c conda-forge python=3.9 simmate
conda activate my_env
# and initialize your database for the first time
simmate database reset
```

<br/>

## Access scratch directory with...
Note, the /y/o/ is decided by the first two letters of your onyen
``` shell
cd /21dayscratch/scr/y/o/youronyen
```

<br/>

## Create a SLURM script with...
``` shell
nano submit.sh
```

<br/>

Paste in the example content. This example is for the 2112_queue partition, but depending on the size of your job and the availability of nodes, you may need to change these inputs.
``` shell
#!/bin/sh

#SBATCH --job-name=NEB
#SBATCH --ntasks=704
#SBATCH --nodes=16
#SBATCH --time=2-00:00
#SBATCH --mem=300g
#SBATCH --partition=2112_queue
#SBATCH --mail-type=ALL
#SBATCH --mail-user=lamcrae@live.unc.edu

simmate workflows run energy-mit -s POSCAR -c "mpirun -n 704 vasp_std > vasp.out"
```

<br/>

## Submit with...
Checklist before submitting:
1. loaded the VASP module
2. activated your conda environment
3. in the temporary working directory (/21dayscratch/scr/y/o/youronyen)
4. created `submit.sh` and edited contents as needed
5. structure file (e.g. `POSCAR`) is present in working directory

Once all of these are met, you can submit with...
``` shell
sbatch submit.sh
```

<br/>

## Monitor progress with... 
``` shell
squeue -u youronyen
```
