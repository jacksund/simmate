# Run a workflow

In this tutorial, you will use the command line to view all available workflows and their settings. Beginners will also be introduced to remote terminals (SSH) and jobs queue (such as SLURM).

> :bulb: For the full tutorial, you will start on your local computer, even if you don't have VASP installed. By the end of the tutorial, you will have switched to a computer with VASP (likely a remote university or federal supercomputer).


## The quick tutorial

> :warning: we assume you have VASP installed and that the `vasp_std` command is in the available path. In the future, we hope to update this tutorial with a workflow that doesn't require VASP or remote Linux cluster. Until then, we apologize for the inconvenience. :cry:

1. Before running a workflow, we must initialize our Simmate database with `simmate database reset`. Your database will be built at `~/simmate/my_env-database.sqlite3`, where "my_env" is the name of your active conda environment.
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
4. Interactively learn about all workflows with `simmate workflows explore`
5. View the settings used for the `static-energy.vasp.mit` workflow with `simmate workflows show-config static-energy.vasp.mit`
6. Copy and paste VASP POTCAR files to the folder `~/simmate/vasp/Potentials`. Be sure to unpack the `tar.gz` files. This folder will have the potentials that came with VASP -- and with their original folder+file names:
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

7. With everything configured, there are now two ways you can submit your workflow using the command-line. This can be done entirely in the CLI, in python, or CLI + a yaml file. Here, let's use a settings file in yaml format:
``` yaml
# In a file named "my_example.yaml".
# Note, different workflows accept different settings here.
workflow_name: static-energy.vasp.mit
structure: POSCAR
command: mpirun -n 5 vasp_std > vasp.out  # OPTIONAL
directory: my_new_folder  # OPTIONAL
```

8. Then run the workflow using the yaml file we just made
``` bash
# now run our workflow from the settings file above
simmate workflows run-yaml my_example.yaml
```

9. Once the workflow completes, you will see files named `simmate_metadata.yaml` and `simmate_summary.yaml` which contains some quick information for you. Other workflows (such as `band-structure` calculations) will also write out plots for you.

10. While the plots and summary files are nice for quick testing, much more useful information is stored in our database. We will cover how to access your database in a later tutorial (05).

> :bulb: Want to customize a specific setting (e.g. set ENCUT to a custom value)? Customizing workflow settings is covered in the "Build Custom Workflows" tutorial. However, try to resist jumping ahead! There are still several important steps to learn before customizing workflows.
