# Reviewing Workflow Results

## Understanding Basic Output Files

Upon completion of your job, you will find additional files in your output. One such file is `simmate_summary.yaml`, which provides a brief summary of your results.

This file contains a subset of the data available in the database:
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

Different workflows may generate additional files and plots. For instance, `electronic-structure` workflows compute a band structure using Materials Project settings and create an image of your final band structure named `band_structure.png`. These additional files and plots, which vary by workflow, facilitate a quick review of your results.

----------------------------------------------------------------------

## Accessing Results via the Website

The `simmate_summary.yaml` file includes a `_WEBSITE_URL_`. To view your results interactively, copy and paste this URL into your browser. Ensure your local server is running before doing so:

``` shell
simmate run-server
```

Then, open the link provided by `_WEBSITE_URL_`:

```
http://127.0.0.1:8000/workflows/static-energy/vasp/mit/1
```

!!! note
    Keep in mind that the server and your database are confined to your local computer. Attempting to access a URL on a computer that doesn't have the same database file will fail. You may need to transfer your database file from the cluster to your local computer. Alternatively, if you wish to access results online, consider switching to a cloud database. This process is explained in a subsequent tutorial.

----------------------------------------------------------------------

## Performing Advanced Data Analysis

Simmate's toolkit and database allow for in-depth analysis of our final structure and complete results. As this requires Python, our next tutorial will guide you through interacting with the toolkit using Python. Subsequent tutorials will cover accessing our database. 

----------------------------------------------------------------------