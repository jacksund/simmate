# Executing our Workflow!

!!! warning
    The following commands will fail unless you have VASP installed on your local computer. :sparkles: **That's perfectly fine!** :sparkles: We'll attempt to run these commands regardless. This will demonstrate how Simmate workflows fail when VASP isn't configured correctly. If VASP isn't installed, you'll encounter an error stating that the `vasp_std` command is unrecognized (like `vasp_std: not found` on Linux). We'll transition to a remote computer with VASP installed in the subsequent section.

----------------------------------------------------------------------

## Executing a Workflow via the Command-line

By default, Simmate runs everything immediately and locally on your desktop. When executing the workflow, it creates a new folder, writes the inputs, runs the calculation, and saves the results to your database.

The command to execute our POSCAR and static-energy/mit workflow is... 

``` shell
simmate workflows run-quick static-energy.vasp.mit --structure POSCAR
```

!!! tip
    The commands in this section may seem long and tedious to write out, and even more challenging to remember. Don't worry, this will become easier once we learn how to submit using YAML files in the next section.

!!! tip
    We refer to this command as `run-quick` because it's typically used for quick testing by advanced users. Most of the time, you'll be using the `run` command, which we will cover below.

By default, Simmate uses the command `vasp_std > vasp.out` and creates a new `simmate-task` folder with a unique identifier (e.g., `simmate-task-j8djk3mn8`).

What if we wanted to modify this command or the directory it's executed in? Remember the output from the `simmate workflows explore` command, which listed parameters for us. We can use any of these to modify how our workflow runs.

For instance, we can change our folder name (`--directory`) and the command used to run VASP (`--command`). With these, we can update our command to:

``` shell
simmate workflows run-quick static-energy.vasp.mit --structure POSCAR --command "mpirun -n 4 vasp_std > vasp.out" --directory my_custom_folder
```

If you encounter any errors, please let our team know by [posting a question](https://github.com/jacksund/simmate/discussions/categories/q-a). 

If not, congratulations :partying_face: :partying_face: :partying_face: !!! You now know how to execute workflows with a single command and understand what Simmate is doing behind the scenes.

----------------------------------------------------------------------

## Executing a Workflow with a Settings File

In the previous section, you may have noticed that our `simmate workflows run` command was becoming quite long and thus difficult to remember. Instead of typing out this lengthy command each time, we can create a settings file that contains all this information. We will write our settings into a `YAML` file, a simple text file. The name of our settings file doesn't matter, so we'll just use `my_settings.yaml`. To create this file, do the following:

``` bash
nano my_settings.yaml
```

... and input the following information ...

``` yaml
workflow_name: static-energy.vasp.mit
structure: POSCAR
command: mpirun -n 4 vasp_std > vasp.out  # OPTIONAL
directory: my_custom_folder  # OPTIONAL
```

This file contains all the information from our `simmate workflows run-quick` command above. But now it's stored in a file that we can read/edit later if needed. To submit this file, we simply run...

``` bash
simmate workflows run my_settings.yaml
```

Your workflow will execute the same as before. It's entirely up to you whether workflows are submitted using a yaml file or the longer command.

!!! tip
    Remember how the command `simmate workflows explore` listed all the parameters for us to use. These are all your options when submitting the workflow. In the example command above, we decided to set two of the optional parameters.

!!! tip 
    Want to customize a specific setting (e.g., set ENCUT to a custom value)? Customizing workflow settings is covered in tutorial 6. However, try to resist jumping ahead! There are still several important steps to learn before customizing workflows.

----------------------------------------------------------------------

## Mastering Workflow Options

In the previous examples, we provided our input structure as a `POSCAR` -- but what if we wanted to use a different format? Or use a structure from a previous calculation or the Materials Project database?

Refer back to the [Parameters](/simmate/getting_started/run_a_workflow/running_the_workflow/) section of our documentation.

Under `structure`, we see that we can use...

- [x] cif or poscar files 
- [x] reference a database entry
- [x] point to a third-party database
- [x] use advanced python objects

For instance, you can try running the following workflow:

``` yaml
workflow_name: static-energy.vasp.mit
structure:
    database_table: MatprojStructure
    database_id: mp-123
command: mpirun -n 4 vasp_std > vasp.out  # OPTIONAL
directory: my_custom_folder  # OPTIONAL
```

Even though we didn't create a structure file, Simmate fetched one for us from the Materials Project database.

----------------------------------------------------------------------