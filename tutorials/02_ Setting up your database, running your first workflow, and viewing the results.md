# Setting up your database, running your first workflow, and viewing the results

## The quick version

1. Initialize our Simmate database with `simmate databate reset`
2. Let's make structure file for Silver (Ag). Name it `POSCAR`, where the contents are...
```
Ag4
1.0
2.951206 0.000000 0.000000
-1.475603 2.555819 0.000000
0.000000 0.000000 9.585754
Ag
4
direct
0.000000 0.000000 0.500000 Ag
0.000000 0.000000 0.000000 Ag
0.666667 0.333333 0.750000 Ag
0.333333 0.666667 0.250000 Ag
```
3. Run a simple workflow with `simmate workflows relaxation-emt POSCAR`
4. Start the simmate test server with `simmate run-server`
5. You can now view the web UI at http://127.0.0.1:8000/
6. In the web UI, navigate to `calculations` --> `relaxations` --> `EMT` to view our results


*Note: this EMT calculation is only meant for testing. We will set up calculations that use more robust softwares like VASP, ABINIT, or LAMMPS in another tutorial.*

## The full tutorial

This tutorial will include...
- activating conda enviornment
- exploring the simmate command and how to navigate its options
- set up your database
- viewing where the database is (.simmate folder) (intro to invisible folders/files and file extensions)
- running a workflow (is there one that doesn't require VASP? XRD maybe?)
- running the Simmate webserver
- viewing results in the web interface
- extra django commands

https://docs.djangoproject.com/en/3.2/topics/settings/#the-django-admin-utility

export DJANGO_SETTINGS_MODULE=simmate.configuration.django.settings
django-admin reset_db
django-admin graph_models -a -o image_of_models.png 
