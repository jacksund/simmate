
# WarWulf

WarWulf is the Warren Lab's Beowulf cluster.

> :bulb: This guide should be used alongside tutorial 02 ([here](https://github.com/jacksund/simmate/blob/main/tutorials/02_%20Run_a_workflow.md#switching-to-a-remote-cluster)).

<br/>

# The Simmate checklist

From the posted requirements:

1. a VASP license for your team **(COMPLETED)**
2. a remote cluster that you have a profile with 
3. VASP installed on the remote cluster **(COMPLETED)**
4. Anaconda installed on the remote cluster **(COMPLETED)**
5. Simmate installed on the remote cluster
6. VASP Potentials in `~/simmate/vasp/Potentials` on the remote cluster **(COMPLETED)**

For the uncompleted requirements:

2. everyone shares the profile "WarrenLab". Ask Scott for the password (scw@email.unc.edu)
5. make your personal environment named `yourname_env` (e.g. `jacks_env`)

<br/>

# Example commands and scripts

Substitute these commands with the ones you see in the main tutorial.

<br/>

## Sign in with...
``` shell
ssh WarrenLab@warwulf.net
```

<br/>

## Load VASP with...
``` shell
module purge
module load gnu11 impi vasp libfabric ucx
```

<br/>

## Call VASP with... 
We don't use `vasp_std` for our default command.
``` shell
vasp > vasp.out 
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
cd /media/synology/user/your_name
```

<br/>

## Create a SLURM script with...
``` shell
nano submit.sh
```

<br/>

And paste in the example content...
``` shell
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

simmate workflows run energy-mit --structure POSCAR --command "mpirun -n 4 vasp_std > vasp.out"
```

<br/>

## Submit with...
Checklist before submitting:
1. loaded the VASP module
2. activated your conda environment
3. in the temporary working directory (/media/synology/user/your_name)
4. created `submit.sh` and edited contents as needed
5. structure file (e.g. `POSCAR`) is present in working directory

Once all of these are met, you can submit with...
``` shell
sbatch submit.sh
```

<br/>

## Monitor progress with... 
We use a short cut for `squeue` with extra info
``` shell
sq
```

You can filter out your jobs using

``` shell
sq | grep yourname
```
