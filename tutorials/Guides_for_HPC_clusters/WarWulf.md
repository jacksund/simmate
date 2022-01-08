
# WarWulf

WarWulf is the Warren Lab's Beowulf cluster.

# Guide

This guide should be used alongside tutorial 02 when switching to a remote cluster ([here](https://github.com/jacksund/simmate/blob/main/tutorials/02_%20Run_a_workflow.md#switching-to-a-remote-cluster)).

## The Simmate checklist

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

## Example commands and scripts

Substitute these commands with the ones you see in the main tutorial.

Sign in with...
```
ssh WarrenLab@warwulf.net
```

Load VASP with...
```
module purge
module load gnu11 impi vasp libfabric ucx
```

Call VASP with... (we don't use `vasp_std` for our default command)
```
vasp > vasp.out 
```

Create your conda env with...
```
conda create -n my_env -c conda-forge python=3.8 simmate
conda activate my_env

# SEE WARNING BELOW -- skip the database reset
```

:warning::warning::warning:
Do **NOT** run the `simmate database reset`. Because we share a username, we share a home directory and database. Calling this command will reset EVERYONE's database. If you think the database needs reset, contact Scott first.
:warning::warning::warning:


Switch to the temporary working directory before submitting:
```
cd /media/synology/user/your_name
```


Create a SLURM script with...
```
nano submit.sh
```

And paste in the example content...
```
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

simmate workflows run energy_mit POSCAR -c "mpirun -n 4 vasp_std > vasp.out"
```

Check list before submitting:
1. loaded the VASP module
2. activated your conda environment
3. in the temporary working directory (/media/synology/user/your_name)
4. created `submit.sh` and editted contents as needed
5. structure file (e.g. `POSCAR`) is present in working directory

Once all of these are met, you can submit with...
```
sbatch submit.sh
```

Monitor progress with... (a short cut for `squeue` with extra info)
```
sq
```
