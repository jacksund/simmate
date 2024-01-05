# Understanding Workflow Stages

!!! note
    This tutorial begins on your local computer, even if you don't have VASP installed. By the end, you'll transition to a computer with VASP, likely a remote university or federal supercomputer.

----------------------------------------------------------------------

## The Four Key Stages

Before initiating any workflows, it's crucial to comprehend the processes occurring behind the scenes. Every workflow undergoes four stages:

- `configure`: Selects our preferred settings for the calculation (like VASP's INCAR settings)
- `schedule`: Determines whether to run the workflow immediately or dispatch it to a job queue (such as SLURM, PBS, or remote computers)
- `execute`: Creates our input files, performs the calculation (like VASP), and scrutinizes the results for errors
- `save`: Stores the results in our database

----------------------------------------------------------------------

## Modifying Each Stage

There are numerous situations where we might want to alter the behavior of these stages. For instance, what if we want to `execute` on a remote computer instead of our local one? Or what if we want to `save` results to a shared cloud database for our entire lab? These configurations are straightforward but require additional setup, so we'll cover them in a future tutorial.

----------------------------------------------------------------------

## Default Simmate Settings
For now, we'll run a workflow using Simmate's default settings. Without any setup, here's what Simmate will do:

- `configure`: Applies the default settings from the requested workflow
- `schedule`: Decides to run the workflow immediately
- `execute`: Performs the calculation directly on our local computer
- `save`: Stores the results on our local computer

----------------------------------------------------------------------

## Pre-Workflow Checklist

Before we can run a workflow, we need to:

- [x] Inform Simmate about the location of our VASP files
- [x] Set up our database for result storage
- [x] Choose a structure for our calculation

The following three sections will address each of these prerequisites.

----------------------------------------------------------------------