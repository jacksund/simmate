
# The 4 stages of a workflow


!!! note
    For the full tutorial, you will start on your local computer, even if you don't have VASP installed. By the end of the tutorial, you will have switched to a computer with VASP (likely a remote university or federal supercomputer).

----------------------------------------------------------------------

## the 4 key stages

Before running any workflows, it is important to understand what's happening behind the scenes. All workflows carry out four steps:

- `configure`: chooses our desired settings for the calculation (such as VASP's INCAR settings)
- `schedule`: decides whether to run the workflow immediately or send off to a job queue (e.g. SLURM, PBS, or remote computers)
- `execute`: writes our input files, runs the calculation (e.g. VASP), and checks the results for errors
- `save`: saves the results to our database

----------------------------------------------------------------------

## changing each stage

There are many different scenarios where we may want to change the behavior of these steps. For example, what if I want to `execute` on a remote computer instead of my local one? Or if I want to `save` results to a cloud database that my entire lab shares? These can be configured easily, but because they require extra setup, we will save them for a later tutorial.

----------------------------------------------------------------------

## simmate defaults
For now, we just want to run a workflow using Simmate's default settings. Without setting anything up, here is what Simmate will do:

- `configure`: take the default settings from the workflow you request
- `schedule`: decides that we want to run the workflow immediately
- `execute`: runs the calculation directly on our local computer
- `save`: saves the results on our local computer

----------------------------------------------------------------------

## check-list before running workflows

Before we can actually run a workflow, we must:

- [x] tell Simmate where our VASP files are
- [x] set up our database so results can be saved
- [x] select a structure for our calculation

The next three sections will address each of these requirements.

----------------------------------------------------------------------
