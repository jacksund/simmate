# LongLeaf

LongLeaf is a Linux-based computing system available for free to researchers across UNC Chapel Hill's campus. Workloads where each job requires a single compute host are best suited for this cluster.

> :bulb: This guide should be used alongside tutorial 02 ([here](https://jacksund.github.io/simmate/getting_started/run_a_workflow/submit_to_a_cluster/)).
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

2. you must create a profile on LongLeaf with your UNC onyen. Directions for this are located [here](https://its.unc.edu/research-computing/longleaf-cluster/).
5. make your personal environment named `yourname_env` (e.g. `jacks_env`)
6. follow tutorial 02 ([here](https://jacksund.github.io/simmate/getting_started/run_a_workflow/configure_potcars/)) to set up VASP potentials

<br/>

# Example commands and scripts

Substitute these commands with the ones you see in the main tutorial.

<br/>

## Sign in with...
``` shell
ssh youronyen@longleaf.unc.edu
```

<br/>

## Load VASP with...
``` shell
module vasp/5.4.4
```

<br/>

## Call VASP with... 
``` shell
# Note, we use 20 cores here but update this to match your submit script
mpirun -n 20 vasp_std > vasp.out
```

<br/>

## Create your conda env with...
``` shell
conda create -n my_env -c conda-forge python=3.10 simmate
conda activate my_env
# and initialize your database for the first time
simmate database reset
```

<br/>

## Access scratch directory with...
``` shell
# Note, the /y/o/ is decided by the first two letters of your onyen
cd /pine/scr/y/o/youronyen
```

<br/>

## Create a SLURM script with...
``` shell
nano submit.sh
```

<br/>

And paste in the example content...
``` shell
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

simmate workflows run energy-mit --structure POSCAR --command "mpirun -n 20 vasp_std > vasp.out"
```

<br/>

## Submit with...
Checklist before submitting:
1. loaded the VASP module
2. activated your conda environment
3. in the temporary working directory (/pine/scr/y/o/youronyen)
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
