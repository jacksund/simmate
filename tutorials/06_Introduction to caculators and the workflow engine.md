# Introduction to caculators and the workflow engine

# The quick tutorial

1. A `Calculator` is an external program that Simmate calls in order to run a calculation (e.g. [VASP](https://vasp.at/), [ABINIT](https://www.abinit.org/), [bader](http://theory.cm.utexas.edu/henkelman/code/bader/), etc.)
2. The `simmate.calculators` module stores all of the code for database tables, input/outputs, common error handlers, and more. 
3. A single calculator run is carried out by a `StagedSupervisedShellTask` or a "`S3Task`". There is some history behind why it's named this way, but here is how the name breaks down:

- `Staged`: the overall calculation is made of three stages (each is a class method)
    1. `setup` = write input files
    2. `execution` = the actual running & monitoring of the program  <--- `Supervised` and `Shell` help describe this stage
    3. `workup` = reading the output files
- `Shell`: the calculator is called through the command-line
- `Supervised`: once the shell command is started, Simmate runs in the background to monitor it for errors

4. All staged are executed through the `run` method. Such as `example_s3task.run()`.
5.  Recall from tutorial 2, that a `Workflow` is made up of 4 steps:

- `configure`: chooses our desired settings for the calculation (such as VASP's INCAR settings)
- `schedule`: decides whether to run the workflow immediately or send off to a job queue (e.g. SLURM, PBS, or remote computers)
- `execute`: writes our input files, runs the calculation (e.g. calling VASP), and checks the results for errors
- `save`: saves the results to our database

and these steps of a `Workflow` can be thought of linking a `S3Task` and a `DatabaseTable`:

- `configure`: default settings are attached to `S3Task` and programmed into it's `S3Task.setup`
- `schedule`: decides when and where `S3Task.run` is called
- `execute`: calls `S3Task.run` which does setup (`S3Task.run` = `S3Task.setup` + `S3Task.execute` + `S3Task.workup`)
- `save`: takes the output of `S3Task` and saves it to the `DatabaseTable`


5. Feel free to add a calculator for a new program if you don't see it in [the available list](https://github.com/jacksund/simmate/tree/main/src/simmate/calculators)!

# The full tutorial

