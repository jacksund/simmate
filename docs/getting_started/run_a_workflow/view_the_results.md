
# Viewing the workflow's results


## Basic output files

Once your job completes, you may notice a few extra files in your output. One of them is `simmate_summary.yaml`, which contains some quick information for you.

The information in this file is a snippet of what's available in the database:
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

Other workflows will also write out plots for you. For example, `electronic-structure` workflows will calculate a band structure using Materials Project settings, and write an image of your final band structure to `band_structure.png`. These extra files and plots vary for each workflow, but they make checking your results nice and quick.

----------------------------------------------------------------------

## The website view

In the `simmate_summary.yaml` file, there is the `_WEBSITE_URL_`. You can copy/paste this URL into your browser and view your results in an interactive format. Just make sure you are running your local server first:

``` shell
simmate run-server
```

Then open the link given by `_WEBSITE_URL_`:

```
http://127.0.0.1:8000/workflows/static-energy/vasp/mit/1
```

!!! note
    Remember that the server and your database are limited to your local computer. Trying to access a URL on a computer that doesn't share the same database file will not work -- so you may need to copy your database file from the cluster to your local computer. Or even better -- if you would like to access results through the internet, then you have to switch to a cloud database (which is covered in a later tutorial).

----------------------------------------------------------------------

## Advanced data analysis

We can analyze our final structure and the full results with Simmate's toolkit and database. Accessing these require Python, so our next tutorial will introduce you to Python by directly interacting with the toolkit. We will then work our way up to accessing our database in a follow-up tutorial.

----------------------------------------------------------------------

