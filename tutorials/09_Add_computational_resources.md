# Add computational resources

In this tutorial, you will learn how to run workflows on distributed computational resources -- with full scheduling and monitoring.

1. [The quick tutorial](#the-quick-tutorial)
2. [The full tutorial](#the-full-tutorial)
    - [A review of concepts](#a-review-of-concepts)
    - [Should I set up my own cluster?](#should-i-set-up-my-own-cluster)
    - [Setting up your scheduler with Prefect](#setting-up-your-scheduler-with-prefect)
    - [Setting up your cluster with Dask](#setting-up-your-cluster-with-dask)
    - [Connecting others to your scheduler](#connecting-others-to-your-scheduler)

<br/><br/>

# The quick tutorial

> :bulb: This tutorial will use the default scheduler/executor, "SimmateExecutor". However, you can also use Prefect and/or Dask to build out your cluster. This is covered in the next tutorial, but it is not recommended at the moment.

1. Be aware that you can share a cloud database *without* sharing computational resources. This flexibility is very important for many collaborations. 

2. Just like with your cloud database, designate a point-person to manage your private computational resources. Everyone else only needs to switch from `run` to `run_cloud`.

3. If your computational resources are distributed on different computers, make sure you have set up a cloud database (see the previous tutorial on how to do this). If you want to schedule AND run things entirely on your local computer (or file system), then you can skip this step.

4. If you have remote resources, make sure you have ALL simmate installations connected to the same database (i.e. your database connection file should be on all resources).

5. If you have custom workflows, make sure you are using a simmate project and all resources have this app installed

> :bulb: If you don't have custom database tables, you can try continuing without this step, but there's no guarantee that the workflow will run properly.

6. Schedule your simmate workflows by switching from the `run` method to the `run_cloud` method. For example, if you are using the command line:
``` bash
simmate workflows run-cloud relaxation.vasp.mit --structure POSCAR
```

> :bulb: This workflow is now scheduled but it won't run until we start a worker.

8. Wherever you'd like to run the workflow, start a worker with:
``` bash
simmate workflow-engine start-singleflow-worker
```

> :warning::warning::warning: If you are on a cluster, start-worker should be called within your submit script (e.g. inside `submit.sh` for SLURM). Don't run workers on the head node! :warning::warning::warning:

9. Note this "singleflow" worker will start, run 1 workflow, then shutdown. If you would like more control over how many workflows are ran or even run a worker endlessly, you can use the command:
``` bash
simmate workflow-engine start-worker
```

10. Scale out your cluster! Start workers anywhere you'd like, and start as many as you'd like. Just make sure you follow steps  4 and 5 for every worker. If you need to start many workers at once, you can use the `start-cluster` command as well.
``` bash
# starts 5 local workers
simmate workflow-engine start-cluster 5
```

11. To control which workers run which workflows, use tags. Workers will only pick up submissions that have matching tags.
``` bash
# when submitting
simmate workflows run-cloud ... -t my_tag -t small-job
```

``` bash
# for the worker
simmate workflow-engine start-worker -t small-job
```

12. To let others use your cluster, simply connect them to the same database.



<br/><br/>

# The full tutorial

<br/>

# A review of concepts

Recall from tutorial 2, there are 4 steps to a workflow:
- `configure`: chooses our desired settings for the calculation (such as VASP's INCAR settings)
- `schedule`: decides whether to run the workflow immediately or send off to a job queue (e.g. SLURM, PBS, or remote computers)
- `execute`: writes our input files, runs the calculation (e.g. calling VASP), and checks the results for errors
- `save`: saves the results to our database

This tutorial will give an overview of how to modify the `schedule` and determine which computer `execute` is called on. Up until now, we have been using the default behavior for these two steps. But now we want to instead do the following:
- `schedule`: submits the workflow to a scheduler queue of many other workflows
- `execute`: run the calculation on a remote cluster

A **scheduler** is something we submit workflows to and controls when to run them. The terms "scheduler" and "executor" are sometimes used interchangeably. As a bunch of workflows are submitted, our scheduler forms a queue and keeps track of which ones to run next. To do this, we can use the built-in `SimmateExecutor`, [Dask](https://docs.dask.org/en/stable/futures.html), or [Prefect](https://www.prefect.io/) as our scheduler. For this tutorial, we will use the `SimmateExecutor` because it is the default one and it's already set up for us.

A **cluster** is a group of computational resources that actually run the workflows. So our scheduler will find whichever workflow should be ran next, and send it to our cluster to run. Clusters are often made up of **workers** -- where a worker is just a single resource and it works through one job at a time. For example, say we have 10 computers (or slurm jobs) that each run one workflow at a time. All computers together are our cluster. Each computer is a worker. At any given time, 10 workflows will be running because each worker will have one it is in charge of. Because we are using the `SimmateExectuor`, we will be using `SimmateWorker`s to set up each worker and therefore our cluster. Set-up for each worker is the same -- whether your resources are on a cloud service, a supercomputer, or just simple desktops.

<br/>

# Should I set up my own cluster?

Before we start... We understand that resource restrictions can be very stingent between labs and companies. So sharing resources is not possible, even in close collaborations. Simmate addresses this issue by making it easy to share a cloud database *without* sharing computational resources. In other words, you can contribute to a shared database without letting others see/access your computational resources.

With that said, each team will likely need to handle their own computational resources, which can be any number of things:
- a university or federal HPC cluster with SLURM, PBS, or some other queue system
- a single node or even a Kubernetes cluster provided by a commercial service like DigitalOcean, GoogleCloud, etc.
- a series of desktop computers that your lab shares
- any combination of these resources

The easiest way to use these resources is to sign on and run a simmate workflow using the `run` method. When this is done, the workflow runs directly on your resource and it will run there immediately. This with Tutorial 2 when we called `simmate workflows run ...`. When on a HPC SLURM cluster, we would run simmate using a `submit.sh` file like this:

```
#!/bin/bash

#SBATCH --output=slurm.out
#SBATCH --nodes=1
#SBATCH --ntasks=2

# make sure you have you activated your conda enviornment 
# and required modules (like vasp) before submitting

simmate workflows run-yaml my_settings.yaml > simmate.out
```

:fire::fire::fire:
If you are only running a few workflows per day (<10), we recommend you stick to running workflows in this way. That is, just calling `simmate workflows run`. Don't overcomplicate things. Go back to tutorial 02 to review these concepts.
:fire::fire::fire:

Alternatively, if your team is submitting hundreds or thousands of workflows at a time, then it would be extremely useful to monitor and orchestrate these workflows using a **scheduler** and **cluster**. Just like with our cloud database in the previous tutorial, you only need ONE person to manage ALL of your computational resources. Once the resources have been set up, the other users can connect using the database connection file (or an API key if you are using Prefect).

If you are that one person for your team, then continue with this tutorial. If not, then you should instead talk with your point person! Using your teams resources should be as easy as switching from the `run` to `run_cloud` method.

</br>

# A check-list for your workers

Now that we know the terms **scheduler**, **cluster**, and **worker** (and also know whether we need these), we can start going through a check list to set everything up:

1. configure your scheduler
2. connect a cloud database
3. connect to the scheduler
4. register all custom projects/apps


**1. The Scheduler**:
If you stick to the "SimmateExecutor", then you're already all good to go! Nothing needs to be done. This is because the queue of job submissions is really just a database table inside the simmate database. Workers will queue this table and grab the first result.

**2. Connecting to a Cloud Database**:
We learned from previous tutorials that simmate (by default) writes results to a local file named `~/simmate/my_env-database.sqlite3`. We also learned that cloud databases let many different computers share data and access the database through an internet connection. Because SQLite3 (the default database engine) is not build for hundreds of connections and we often use separate computers to run workflows, you should build a cloud database. Therefore, don't skip tutorial 08 where we set up a cloud database!

**3. Connecting to the Scheduler**
Because we are using the "SimmateExecutor" all we need is a connection to the cloud database. All you need to do make sure ALL of your computational resources are connected to the cloud database you configured. If your workers aren't picking up any of your workflow submissions, it's probably because you didn't connect them properly.

**4. Connecting custom projects**

> :warning: Because SimmateExecutor uses cloudpickle when submitting tasks, many custom workflows will work just fine without this step. Our team is still working how to guide users and make this as easy as possible. For now, we suggest just trying out your workflow when you skip this step -- as most times it will work. If not, then the text below explains why.

If you have custom database tables or code, it's important that (a) the cloud database knows about these tables and (b) your remote resources can access your custom code. Therefore, your custom project/app should be installed and accessible by all of your computation resources. Be sure to `pip install your-cool-project` for all computers.


</br>

# Setting up your cluster and workers

After you go through the check-list above, you're ready to start a worker!

Scheduling a workflow is straight-forward. Simply change all your scripts and commands from the `run` method to the `run_cloud` method. For example, if you are using the command line:
``` bash
simmate workflows run-cloud relaxation.vasp.mit --structure POSCAR
```

This schedules your workflow, but it won't run yet. It is simply sitting in the queue and waiting for a worker to pick it up. Once we start a worker, then it will actually run.

Whereever you'd like to run the workflow, start a worker with:
``` bash
simmate workflow-engine start-singleflow-worker
```
> :warning::warning::warning: If you are on a cluster, start-worker should be called within your submit script (e.g. inside `submit.sh` for SLURM). Don't run workers on the head node! :warning::warning::warning:

When you run this "singleflow" worker, you'll notice that the Worker will start, run 1 workflow, then shutdown. This is the recommend approach for HPC clusters because it follow best practices for sharing resources. You don't want a worker hogging computational resources if there aren't any workflows scheduled to run! 

However, if you would like more control over how many workflows are ran or even run a worker endlessly, you can use the command:
``` bash
simmate workflow-engine start-worker
```

For example, if your team runs many mini workflows that are under 5 minutes, starting/stopping workers could be a pain (sometimes it can take simmate up to 10 seconds to set everything up). That's a significant overhead and wasted computation time. To overcome this, we would run a worker that shuts down after 10 workflows or if the queue is empty:
``` bash
simmate workflow-engine start-worker --nitems_max 10 --close_on_empty_queue true
```

If you need to start many workers at once, you can use the `start-cluster` command as well.
``` bash
# starts 5 local workers
simmate workflow-engine start-cluster 5
```

</br>

# Controlling what workflows are ran by each worker

> :warning: The full guide for custom workers is still being written. See workflow "tags" for more information.

</br>

# Connecting others to your scheduler

If they are connected to your database, then they're good to go! Other schedulers like Prefect or Dask require extra setup.

</br>

# You did it!

:fire::fire::fire::fire::fire::fire:

If you made it to this point, you're pretty much a Simmate expert! 

Any other guides and tutorials will be in the API documentation. We hope you see the potential Simmate has to offer the larger materials community! With a powerful framework like Simmate in hand, anything is possible. In other words...

**"The ceiling is the roof" -Michael Jordan**

Have fun coding and always be sure to ask for help/feedback when you need it.

:fire::fire::fire::fire::fire::fire:
