# Explore & Run Workflows

## Quick Start

!!! tip
    The majority of this guide covers initial setup for first-time users. For subsequent workflow runs, only steps 8-10 are necessary.

1. Initialize your Simmate database, which will be created at `~/simmate/my_env-database.sqlite3` and where `my_env` is the name of your active conda environment:
```bash
simmate database reset
```

2. Create a structure file for sodium chloride, which we will use to practice calculations. Name it `POSCAR` and fill it with the following content:
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

3. Use the following command to view a list of all available workflows:
```bash
simmate workflows list-all
```

4. Learn about all workflows interactively with the following command:
``` bash
simmate workflows explore
```

    !!! note
        There are a variety of software options for QM, DFT, or other analyses (e.g., VASP, Abinit, QE, LAMMPS, etc.). In this tutorial, we will use Quantum Espresso because we have Docker images for those who don't have it installed. If you prefer another program, check the `Apps` section in our guides for specific instructions.


5. Make sure you have Quantum Espresso (QE) installed using one of two options:
      - (*for beginners*) Install [Docker-Desktop](https://www.docker.com/products/docker-desktop/). Then run the following command:
          ``` bash
          simmate config update "quantum_espresso.docker.enable=True"
          ```
      - (*for experts*) Install QE using [offical guides](https://www.quantum-espresso.org/) and make sure `pw.x` is in the path

        !!! tip
            If you choose Docker and need help, see our guides [here](/simmate/getting_started/workflows/configure_qe/#1-install-qe-using-docker) for installation and common errors.

6. To run calculations with QE, we need psuedopotentials. Simmate helps load these from the popular [SSSP library](https://www.materialscloud.org/discover/sssp/):
``` bash
simmate-qe setup sssp
```

7. Make sure QE is fully configured and ready to use:
``` bash
simmate config test quantum_espresso
```

8. With everything configured, you can submit your workflow using the website interface, command-line, or Python. Here, we'll use a settings file in YAML format. Create a file named `example.yaml` with the following content:
``` yaml
workflow_name: static-energy.quantum-espresso.quality00
structure: POSCAR
```

9. Run the workflow configuration file we just created:
``` bash
simmate workflows run example.yaml
```

10. The run will create a new folder (e.g. `simmate-task-abcd1234`) for your run. Inside, you'll find files named `simmate_metadata.yaml` and `simmate_summary.yaml` which contain some quick information. Some workflows (like `band-structure` calculations) will also generate plots for you.

    !!! tip
        While the plots and summary files are useful for quick testing, more detailed information is stored in our database. We'll cover how to access your database in a subsequent tutorial.
