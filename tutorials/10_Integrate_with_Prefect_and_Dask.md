# Integrate with Prefect and Dask

> :warning::warning::warning: We do not recommend this tutorial for users at the moment. This tutorial is for Prefect v1, but much of Simmate now depends on Prefect v2. As we adjust to the new backend, parts of this tutorial may be broken and recommended procedures are subject to change. :warning::warning::warning: 

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
# --------------------------------------------------------------------------------------

# STEP 1: Configure our Dask Cluster.

from dask_jobqueue import SLURMCluster

cluster = SLURMCluster(
    #
    # General options
    scheduler_options={"port": 8786},
    local_directory="~",
    #
    #
    # Dask Worker Options
    cores=1,
    processes=1,
    memory="4GB",
    # REQUIRED: Make sure you preload this script!
    extra=["--preload simmate.configuration.dask.connect_to_database"],  
    #
    #
    # SLURM Job Options
    job_cpu=18,
    job_mem="50GB",
    job_extra=[
        "--output=slurm-%j.out",
        "-N 1",
    ],
    walltime="300-00:00:00",
    queue="p1",  # this is the name of the SLURM queue/partition
    env_extra=["module load vasp;"],  # our workflow requires the vasp module to be loaded
)

# Scale the cluster to the number of SLURM jobs that you'd like
cluster.scale(10)

# --------------------------------------------------------------------------------------

# STEP 2: Configure our Prefect Agent and start submitting workflows!

from prefect.agent.local import LocalAgent
from simmate.configuration.prefect.connect_to_dask import set_default_executor

# We want Prefect to use our Dask Cluster to run all of the workflow tasks. To
# tell Prefect to do this, we wrote a helper function that ships with Simmate.
set_default_executor(cluster.scheduler.address)

# Start our cluster! Our cluster's name is Warwulf, so we use that here.
agent = LocalAgent(
    name="WarWulf",
    labels=["WarWulf"],
)

# Now we can start the Prefect Agent which will run and search for jobs and then
# submit them to our Dask cluster.
agent.start()
# NOTE: this line will run endlessly unless you set a timelimit in the LocalAgent above

# --------------------------------------------------------------------------------------
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

# Setting up your scheduler with Prefect

The first half of this section is just a replica of Prefect's tutorial, but rewritten in a condensed format. If you prefer, you can use their tutorial instead: [Introduction to Prefect Orchestration](https://docs.prefect.io/orchestration/getting-started/quick-start.html)

With Prefect as our scheduler, we have two options on how to set this up: Prefect Cloud or Prefect Server. They give a guide on which to choose [here](https://docs.prefect.io/orchestration/server/overview.html#prefect-server-vs-prefect-cloud-which-should-i-choose), but to summarize:
- Prefect Server is free and open-source, but it requires you set up a server and manage it independently
- Prefect Cloud is free for your first 20,000 workflow tasks each month (here's [their pricing page](https://www.prefect.io/pricing)) and all set up for you

Our team uses Prefect Cloud and recommends that beginners do the same. Unless you are running dozens of [evolutionary searches] per month, you won't come close to the 20,000 workflow task-run limit. This tutorial will continue with Prefect Cloud, but if you decide on [Prefect Server](https://docs.prefect.io/orchestration/server/overview.html), you'll have to set that up before continuing.

Go ahead and sign in to [Prefect Cloud](https://universal.prefect.io/) (use your github account if you have one!). Everything will be empty to start, so we want to add all of Simmate's workflows to our interface here. To do this, we need an API key, which acts like a username and password. It's how we tell python that we now have a Prefect account.

To get your API key, go to Prefect Cloud's homepage and navigate to `User` -> `Account Settings` -> `API Keys` -> `Create An API Key`. Copy the created API key.

On your computer, open a terminal and make sure you have your conda enviornment active. Prefect is already installed because the installation of Simmate did it for us. So run the command: `prefect backend cloud`. This just tells prefect that we decided to use their scheduler. Next, run the command `prefect auth login --key example_key_h123j2jfk` where you replace the end text with your copied API KEY. We can now use Simmate to access your cloud and submit workflows for us!

To get started, we need to add all of our workflows to Prefect. This is done with `simmate workflow-engine setup-cloud`. After running this, you should see all of the workflow in your Prefect Cloud now! 

If you were to use the `simmate workflows run` command that we've been using, you'll notice it still runs directly on your computer. To instead submit it to Prefect Cloud, use the command  `simmate workflows run-cloud` instead. So for an example workflow, the full command would be... `simmate workflows run-cloud relaxation_mit POSCAR`. 

When you use `run-cloud`, the workflow run shows up in your Prefect Cloud, but it's not running. That is because we need a Prefect "Agent" -- an Agent simply checks for workflows that need to be ran and submits them to a cluster of computational resources. Let's start a Prefect Agent with all default settings (no cluster is attached yet), which means it will simply run the workflow on whichever computer the agent is on. To do this, run the command `prefect agent local start`. You'll see it pick up the workflow we submitted with `run-cloud` and run it. Even after the job completes, the agent will continue to run. So if you submit a new workflow, it will run it as well.

We skimmed over a lot of the fundamentals for Prefect here, so we highly recommend going through [Prefect's guides and tutorials](https://docs.prefect.io/orchestration/getting-started/quick-start.html). Spending a day or two on this will save you a lot of headache down the road.

</br>

# Setting up your cluster with Dask

Because there is such a diverse set of computational resources that teams can have, we can't cover all setup scenarios in this tutorial. Instead, we will go through some examples of submitting Simmate workflows to a Dask cluster. This will all be on your local computer. For switching to remote resources (and job queue clusters like SLURM), we can only point you to key tutorials and documentation on how to set up your cluster. You can [ask our team](https://github.com/jacksund/simmate/discussions/categories/q-a) which setup is the best fit for your team, and we'll try to guide you through the process. Setting up your cluster shouldn't take longer than a hour, so post a question if you're struggling!

Here are some useful resources for setting up a cluster with Dask. We recommend going through these before trying to use Dask with Simmate:
- [Introduction to Dask Futures](https://docs.dask.org/en/latest/futures.html)
    - This is the best tutorial to start with! Then go through [their example](https://examples.dask.org/futures.html). Dask can do a lot, but Simmate only really uses this feature. If you understand how to use the `client.submit`, then you understand how Simmate is using Dask :smile: 
- [Introduction to Dask Jobqueue](http://jobqueue.dask.org/en/latest/)
    - If you use a queue system like PBS, Slurm, MOAB, SGE, LSF, and HTCondor, then this will show you how to set up a cluster on your resource.

Here's a simple example of using Dask to run a function that "sleeps" for 1 second
```python
import time

# This loop will take 60 seconds to complete
for n in range(60):  # run this 60 times
    time.sleep(1)  # sleeps 1 second
    
# Now we switch to using Dask
from dask.distributed import Client

client = Client()

# Futures are basically our "job_id". They let us check the status and result
futures = []
for n in range(60):  # run this 60 times
    # submits time.sleep(1) to Dask. pure=False tells Dask to rerun each instead
    # of loading past results from each time.sleep(1). 
    future = client.submit(time.sleep, 1, pure=False) 
    futures.append(future)

# now wait for all the jobs to finish
# This will take much less than 60 seconds!
results = [future.result() for future in futures]
```

We'll now try using Dask to run our Simmate workflows.

### In serial (one item at time)

Let's start with how we've been submitting workflows: using `workflow.run`. This runs the workflow immediately and on your local computer. If we were to run a workflow of many structures, only one workflow would run at a time. Once a workflow completes, it moves on to the next one:

```python
from simmate.workflows import example_workflow

for structure in structures:
    result = example_workflow.run(structure=structure)
```

### In parallel (many workflows at once)
To use your entire computer and all of its CPUs, we can set up a Dask cluster. There's one added thing you need to do though -- and that's make sure all of Dask workers are able to connect to the Simmate database. This example let's you submit a bunch of workflows and multiple workflows can run at the same time. You can do this with...

```python
# first setup Dask so that it can connect to Simmate
from dask.distributed import Client
client = Client(preload="simmate.configuration.dask.connect_to_database")

# now submit your workflows and 
futures = []
for structure in structures:
    future = client.submit(example_workflow.run, structure=structure)
    
result = future.result()

# wait for all workflows to finish
# you can monitor progress at http://localhost:8787/status
```

### In parallel (many tasks from a single workflow at once)
 But what if you want to run a single workflow with all of it's tasks in parallel? To do that, we use...

```python
# first setup Dask so that it can connect to Simmate
from dask.distributed import Client
client = Client(preload="simmate.configuration.dask.connect_to_database")

# Tell Prefect that we should submit each task to Dask
from prefect.executors import DaskExecutor
example_workflow.executor = DaskExecutor(address=client.scheduler.address)

# now run your workflow and wait for it to finish
result = example_workflow.run()
```

### Connecting your Dask cluster to your Prefect Agent

Once you learned how to set up your Dask cluster, the next step is tell Prefect where it is. You can always write your python script as two steps:

1. Configure and then start your Dask Cluster.
2. Configure and then start your Prefect Agent, which will start submitting workflows!

In the future, we hope to have more convenient methods through the command-line, but these features are not complete yet. 

</br>

# Connecting others to your scheduler

Once you've set up your scheduler with Prefect and cluster with Dask, your team members simply need to connect to Prefect Cloud to submit their workflows. Generate an API key for them. Then they can complete step 9 of [the quick tutorial](#the-quick-tutorial) (above).

Just remember... `workflow.run()` in python and `simmate workflows run` in the command-line will still run the workflow locally and right away. `workflow.run_cloud()` in python and `simmate workflows run-cloud` in the command-line will submit your workflow to Prefect Cloud.
