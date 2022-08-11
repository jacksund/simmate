> :warning::warning::warning: This tutorial is for Prefect v1, but much of Simmate now depends on Prefect v2. As we adjust to the new backend, parts of this tutorial may be broken and recommended proceedures are subject to change.

# Add computational resources

In this tutorial, you will learn how to run workflows on distributed computational resources -- with full scheduling and monitoring.

1. [The quick tutorial](#the-quick-tutorial)
2. [The full tutorial](#the-full-tutorial)
    - [A review of concepts](#a-review-of-concepts)
    - [Should I set up my own cluster?](#should-i-set-up-my-own-cluster)
    - [Setting up your scheduler with Prefect](#setting-up-your-scheduler-with-prefect)
    - [Setting up your cluster with Dask](#setting-up-your-cluster-with-dask)
    - [Connecting others to your scheduler](#connecting-others-to-your-scheduler)

> :warning: For beginners, this will be the most difficult part of setting up Simmate -- but it is entirely optional. Be sure to read the section on [Should I set up my own cluster?](#should-i-set-up-my-own-cluster). There are many ways to set up your resources and caviats to each (especially if you are using university or federal supercomputers). While python experts should be able to learn Prefect and Dask quickly, we strongly urge beginners to get advice from our team. If you struggle to follow along with this tutorial, [post a question](https://github.com/jacksund/simmate/discussions/categories/q-a) or email us directly (simmate.team@gmail.com).


<br/><br/>

# The quick tutorial

> :bulb: [prefect](https://github.com/PrefectHQ/prefect), [dask](https://github.com/dask/distributed), and [dask_jobqueue](https://github.com/dask/dask-jobqueue) will be already installed for you because they are dependencies of Simmate

1. Be aware that you can share a cloud database *without* sharing computational resources. This flexibility is very important for many collaborations. 
2. Just like with your cloud database, designate a point-person to manage your private computational resources. Everyone else can skip to step 9.
3. Either sign in to [Prefect Cloud](https://universal.prefect.io/) (recommended) or setup a [Prefect Server](https://docs.prefect.io/orchestration/server/overview.html).
4. Connect to your server with the following steps (this is from [Prefect's tutorial](https://docs.prefect.io/orchestration/getting-started/set-up.html)):
    - On Prefect Cloud's homepage, go to `User` -> `Account Settings` -> `API Keys` -> `Create An API Key`
    - Copy the created key
    - set your Prefect backend with the command `prefect backend cloud`
    - tell Prefect your key with the command `prefect auth login --key example_key_h123j2jfk`
5. Register all Simmate workflows with Prefect using the command `simmate workflow-engine setup-cloud`
6. Test that Prefect is configured properly with the following steps (this will run the workflow locally):
    - run the command `prefect agent local start` (note that this will run endlessly and submit all workflows in parallel. use `crtl+C` to stop)
    - in a separate terminal, rerun our workflow from tutorial 2 with `run-cloud` instead of `run` (so `simmate workflows run-cloud relaxation_mit POSCAR`)
7. Set up your computational resources using Dask (and if needed, Dask JobQueue). There are MANY options for this, which are covered in the [`simmate.workflow_engine`](https://github.com/jacksund/simmate/tree/main/src/simmate/workflow_engine) module. Take the time to read the documentation here. But as an example, we'll set up a SLURM cluster and then link it to a Prefect agent. Note, if you want to run workflows with commands like `mpirun -n 18 vasp_std > vasp.out`, then limit the Dask worker to one core while having the SLURM job request more cores. The resulting python script will look something like this:
```python

```
8. Test out your cluster by running `simmate workflows run-cloud relaxation_mit POSCAR` in a separate terminal (submit this a bunch if you'd like to). If you'd like to limit how many workflows of a given tag (e.g. "WarWulf" above) run in parallel, set the concurrency limit in Prefect cloud [here](https://cloud.prefect.io/team/flow-concurrency).
9. To let others use your cluster, simply add them to your Prefect Cloud and give them an API key. They just need to do the following:
    - set your Prefect backend with the command `prefect backend cloud`
    - tell Prefect your key with the command `prefect auth login --key example_key_h123j2jfk`
    - try submitting a workflow with `simmate workflows run-cloud relaxation_mit POSCAR`

<br/><br/>

# The full tutorial

<br/>

# A review of concepts

Recall from tutorial 2, there are 4 steps to a workflow:
- `configure`: chooses our desired settings for the calculation (such as VASP's INCAR settings)
- `schedule`: decides whether to run the workflow immediately or send off to a job queue (e.g. SLURM, PBS, or remote computers)
- `execute`: writes our input files, runs the calculation (e.g. calling VASP), and checks the results for errors
- `save`: saves the results to our database

This tuturial will give an overview of how to modify the `schedule` and determine which computer `execute` is called on. Up until now, we have been using the default behavior for these two steps. But now we want to instead do the following:
- `schedule`: submits the workflow to a scheduler queue of many other workflows
- `execute`: run the calculation on a remote cluster

A scheduler is something we submit workflows to and controls when to run them. As a bunch of workflows are submitted, our scheduler forms a queue and keeps track of which ones to run next. We will use [Prefect](https://www.prefect.io/) as our scheduler. 

A cluster is a group of computational resources that actually run the workflows. So our scheduler will find whichever workflow should be ran next, and send it to our cluster to run. Clusters are often made up of "workers" -- where a worker is just a single resource and it works through one job at a time. For example, if we had a cluster made up of 10 desktop computers, each computer would run a workflow and once finished ask the scheduler for the next workflow to run. At any given time, 10 workflows will be running. We'll use Dask to set up our cluster, whether your resources are on the cloud, a supercomputer, or just simple desktops.

<br/>

# Should I set up my own cluster?

Before we start... We understand that resource restrictions can be very stingent between labs and companies. So sharing resources is not possible, even in close collaborations. Simmate addresses this issue by making it easy to share a cloud database *without* sharing computational resources. In other words, you can contribute to a shared database without letting others see/access your computational resources.

With that said, each team will likely need to handle their own computational resources, which can be any number of things:
- a university or federal HPC cluster with SLURM, PBS, or some other queue system
- a single node or even a Kubernetes cluster provided by a commercial service like DigitalOcean, GoogleCloud, etc.
- a series of desktop computers that your lab shares
- any combination of these resources

The easiest way to use these resources is to sign on and run simmate directly on it. When this is done, the workflow runs directly on your resource and it will run there immediately. We've already see this with Tutorial 2 when we called `simmate workflows run ...`. Just use that on your new resource to start! (for help signing on to remote supercomputers and installing anaconda, be sure to ask the cluster's IT team).

As another example, you can submit a workflow to a SLURM cluster with a submit.sh file like this:
```
#!/bin/bash

#SBATCH --output=slurm.out
#SBATCH --nodes=1
#SBATCH --ntasks=2

# make sure you have you activated your conda enviornment 
# and required modules before submitting

simmate workflows run-cloud relaxation_mit POSCAR > simmate.out
```

:fire::fire::fire:
If you are only running a few workflows per day (<10), we recommend you stick to running workflows in this way. That is, just calling `simmate workflows run`. Don't overcomplicate things.
:fire::fire::fire:

Alternatively, if your team is submitting hundreds or thousands of workflows at a time, then it would be extremely useful to monitor and orchestrate these workflows. To do this, we will use Prefect and Dask. Just like with our cloud database in the previous tutorial, you only need ONE person to manage ALL of your computational resources. Once the resources have been set up, the other users can connect using API key (which is essentially a username+password).

</br>

# Connecting others to your scheduler

Once you've set up your scheduler with Prefect and cluster with Dask, your team members simply need to connect to Prefect Cloud to submit their workflows. Generate an API key for them. Then they can complete step 9 of [the quick tutorial](#the-quick-tutorial) (above).

Just remember... `workflow.run()` in python and `simmate workflows run` in the command-line will still run the workflow locally and right away. `workflow.run_cloud()` in python and `simmate workflows run-cloud` in the command-line will submit your workflow to Prefect Cloud.
