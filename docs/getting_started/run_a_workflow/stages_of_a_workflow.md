
# The 4 stages of a workflow

Before running any workflows, it is important to understand what's happening behind the scenes. All workflows carry out four steps:

- `configure`: chooses our desired settings for the calculation (such as VASP's INCAR settings)
- `schedule`: decides whether to run the workflow immediately or send off to a job queue (e.g. SLURM, PBS, or remote computers)
- `execute`: writes our input files, runs the calculation (e.g. VASP), and checks the results for errors
- `save`: saves the results to our database

There are many different scenarios where we may want to change the behavior of these steps. For example, what if I want to `execute` on a remote computer instead of my local one? Or if I want to `save` results to a cloud database that my entire lab shares? These can be configured easily, but because they require extra setup, we will save them for a later tutorial.

For now, we just want to run a workflow using Simmate's default settings. Without setting anything up, here is what Simmate will do:

- `configure`: take the default settings from the workflow you request
- `schedule`: decides that we want to run the workflow immediately
- `execute`: runs the calculation directly on our local computer
- `save`: saves the results on our local computer

Before we can actually run this workflow, we must:

1. tell Simmate where our VASP files are
2. set up our database so results can be saved
3. select a structure for our calculation

The next three sections will address each of these requirements.
