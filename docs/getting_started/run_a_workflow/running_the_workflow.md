
# Finally running our workflow!

!!! warning
    Unless you have VASP installed on your local computer, these next commands will fail. :sparkles: **That is okay!** :sparkles: Let's go ahead and try running these commands anyways. It will be helpful to see how Simmate workflows fail when VASP is not configured properly. If you don't have VASP installed, you'll see an error stating that the `vasp_std` command isn't known (such as `vasp_std: not found` on Linux). We'll switch to a remote computer with VASP installed in the next section.


## Running a workflow using the command-line

The default Simmate settings will run everything immediately and locally on your desktop. When running the workflow, it will create a new folder, write the inputs in it, run the calculation, and save the results to your database.

The command to do this with our POSCAR and static-energy/mit workflow is... 

``` shell
simmate workflows run-quick static-energy.vasp.mit --structure POSCAR
```

!!! tip
    You'll notice the commands in this section are long a pain to write out. Plus even more difficult to remember. Don't worry, this will go away once we learn how to submit using YAML files in the next section

!!! tip
    We call this command `run-quick` becuase it is (typically) only ever used in quick testing by advanced users. 99% of the time, you'll be using the `run` command, which we will cover below

By default, Simmate uses the command `vasp_std > vasp.out` and creates a new `simmate-task` folder with a unique identifier (ex: `simmate-task-j8djk3mn8`).

What if we wanted to change this command or the directory it's ran in? Recall the output from the `simmate workflows explore` command, which listed parameters for us. We can use any of these to update how our worklfow runs.

For example, we can change our folder name (`--directory`) as well as the command used to run VASP (`--command`). Using these, we can update our command to this:

``` shell
simmate workflows run-quick static-energy.vasp.mit --structure POSCAR --command "mpirun -n 4 vasp_std > vasp.out" --directory my_custom_folder
```

If any errors come up, please let our team know by [posting a question](https://github.com/jacksund/simmate/discussions/categories/q-a). 

If not, congrats :partying_face: :partying_face: :partying_face: !!! You now know how to run workflows with a single command and understand what Simmate is doing behind the scenes.


## Running a workflow using a settings file

In the last section, you probably noticed that our `simmate workflows run` command was getting extremely long and will therefore be difficult to remember. Instead of writing out this long command every time, we can make a settings file that contains all of this information. Here, we will write our settings into a `YAML` file, which is just a simple text file. The name of our settings file doesn't matter, so here we'll just use `my_settings.yaml`. To create this file, complete the following:

``` bash
nano my_settings.yaml
```

... and write in the following information ...

``` yaml
workflow_name: static-energy.vasp.mit
structure: POSCAR
command: mpirun -n 4 vasp_std > vasp.out  # OPTIONAL
directory: my_custom_folder  # OPTIONAL
```

Note that this file contains all of the information that was in our `simmate workflows run-quick` command from above! But now we have it stored in a file that we can read/edit later on if we need to. To submit this file, we simply run...

``` bash
simmate workflows run my_settings.yaml
```

And your workflow will run the same as before! Note, it is entirely up to you whether workflows are ran submit using a yaml file or using the longer command.

!!! tip
    recall from earlier how the command `simmate workflows explore` printed out all of the parameters for us to use. These are all of your options when sumbitting the workflow. In the example command above, we decided to set two of the optional parameters

!!! tip 
    Want to customize a specific setting (e.g. set ENCUT to a custom value)? Customizing workflow settings is covered in tutorial 6. However, try to resist jumping ahead! There are still several important steps to learn before customizing workflows.

