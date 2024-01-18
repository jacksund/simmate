# Running a Workflow

!!! tip
    This guide covers how to run workflows with a YAML file + the command line. But keep in mind, there are other ways to run your workflows -- such as using the website interface, a python script, or `run-quick` in the command line. 

----------------------------------------------------------------------

## 1. Recap

In the previous sections, we accomplished the following prerequisites for running a workflow:

- [x] Configured our database for storing results
- [x] Created a structure file to use as input
- [x] Selected a workflow to use (`static-energy.quantum-espresso.quality00`)
- [x] Selected QE as our DFT software & configured it 

Now let's run our workflow!

----------------------------------------------------------------------

## 2. Create a config file

Rather than have super long command with all of our settings, we will write our settings into a `YAML` file. 

The name of our settings file doesn't matter, so we'll just use `example.yaml`. Create this file and add the following to it:

``` yaml
# in example.yaml
workflow_name: static-energy.quantum-espresso.quality00
structure: POSCAR
```

----------------------------------------------------------------------

## 3. Submit the workflow

Make sure both your `POSCAR` file AND `example.yaml` files are in the same folder as your command-line's working directory. Then start your workflow run with the following command: 

``` shell
simmate workflows run example.yaml
```

When running the workflow, it creates a new folder (e.g., `simmate-task-abcd1234`), writes the inputs, runs the calculation, and saves the results to your database.

!!! tip
    Depending on your laptop specs, this calculation can take >1 minute to finish.

----------------------------------------------------------------------

### 4. View results

Once you're workflow finishes, you will find additional files in your output folder (e.g., `simmate-task-abcd1234`). One such file is `simmate_summary.yaml`, which provides a brief summary of your results:

``` yaml
_DATABASE_TABLE_: StaticEnergy
_TABLE_ID_: 1
_WEBSITE_URL_: http://127.0.0.1:8000/workflows/static-energy/vasp/mit/1
band_gap: 4.9924
chemical_system: Cl-Na
computer_system: digital-storm
conduction_band_minimum: 4.306
corrections: []
created_at: 2022-09-10 14:32:35.857088+00:00
density: 2.1053060843576104
density_atomic: 0.04338757298280908
directory: /home/jacksund/Documents/spyder_wd/simmate-task-e9tddsyw
energy: -27.25515165
energy_fermi: -0.63610593
energy_per_atom: -3.40689395625
formula_anonymous: AB
formula_full: Na4 Cl4
formula_reduced: NaCl
id: 42
is_gap_direct: true
lattice_stress_norm: 8.428394235089161
lattice_stress_norm_per_atom: 1.0535492793861452
nelements: 2
nsites: 8
run_id: 3a1bd23f-705c-4947-96fa-3740865ed12d
site_force_norm_max: 1.4907796617877505e-05
site_forces_norm: 2.257345786537809e-05
site_forces_norm_per_atom: 2.8216822331722614e-06
spacegroup_id: 225
updated_at: 2022-09-10 14:33:09.419637+00:00
valence_band_maximum: -0.6864
volume: 184.38459332974767
volume_molar: 13.87987468758872
workflow_name: static-energy.vasp.mit
workflow_version: 0.10.0
```

Different workflows may generate additional files and plots. For instance, `electronic-structure` workflows compute a band structure and create an image of your final band structure named `band_structure.png`. These additional files and plots, which vary by workflow, facilitate a quick review of your results.

In the next set of tutorials, we will explore our database and the other data stored in it.

----------------------------------------------------------------------

## 4. Mastering parameters

### a. Basic

What if we wanted to modify the directory the workflow is ran in? Don't forget about the `simmate workflows explore` command, which listed parameters for us. We can use any of these to modify how our workflow runs.

For instance, we can change our folder name (`directory`). With this, we can update our `example.yaml` to:

``` yaml
workflow_name: static-energy.quantum-espresso.quality00
structure: POSCAR
directory: my_custom_folder  # OPTIONAL
```

and re-run:

``` shell
simmate workflows run example.yaml
```

### b. Advanced

In the previous examples, we provided our input structure as a `POSCAR` -- but what if we wanted to use a different format? Or use a structure from a previous calculation or the Materials Project database?

When we go to the `Parameters` documentation, we see that `structure` input accepts...

- [x] cif or poscar files 
- [x] pointers to a database entry
- [x] pointers to a third-party database
- [x] advanced python objects

For instance, you can try running the following workflow:

``` yaml
workflow_name: tatic-energy.quantum-espresso.quality00
structure:
    database_table: MatprojStructure
    database_id: mp-22862
```

Even though we didn't create a structure file, Simmate fetched one for us from the Materials Project database.

----------------------------------------------------------------------
