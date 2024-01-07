# Run a Workflow

!!! danger
    This tutorial assumes that you have VASP installed and that the `vasp_std` command is accessible in your path. We plan to update this tutorial in the future with a workflow that doesn't require VASP or a remote Linux cluster. We apologize for any inconvenience this may cause.

## Quick Tutorial

1. Initialize your Simmate database before running a workflow. Your database will be created at `~/simmate/my_env-database.sqlite3`, where "my_env" is the name of your active conda environment:
```bash
simmate database reset
```

2. Create a structure file for tablesalt (NaCl) to practice calculations. Name it `POSCAR` and fill it with the following content...
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

5. View the settings used for the `static-energy.vasp.mit` workflow with `show-config`
``` bash
simmate workflows show-config static-energy.vasp.mit
```

6. Copy and paste VASP POTCAR files into the `~/simmate/vasp/Potentials` folder. Make sure to unpack the `tar.gz` files. This folder should contain the potentials that came with VASP, maintaining their original folder and file names:
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

7. Once everything is configured, you can submit your workflow using the command-line. This can be done either in the CLI or in Python. Here, we'll use a settings file in YAML format:
``` yaml
# In a file named "my_example.yaml".
# Note, different workflows accept different settings here.
workflow_name: static-energy.vasp.mit
structure: POSCAR
command: mpirun -n 5 vasp_std > vasp.out  # OPTIONAL
directory: my_new_folder  # OPTIONAL
```

8. Run the workflow configuration file we just created
``` bash
simmate workflows run my_example.yaml
```

9. Once the workflow is complete, you'll find files named `simmate_metadata.yaml` and `simmate_summary.yaml` which contain some quick information. Other workflows (like `band-structure` calculations) will also generate plots for you.

10.  While the plots and summary files are useful for quick testing, more detailed information is stored in our database. We'll cover how to access your database in a subsequent tutorial.
