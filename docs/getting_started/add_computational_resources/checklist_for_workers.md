
# A check-list for your workers

Now that we know the terms **scheduler**, **cluster**, and **worker** (and also know whether we need these), we can start going through a check list to set everything up:

- [x] configure your scheduler
- [x] connect a cloud database
- [x] connect to the scheduler
- [x] register all custom projects/apps


## 1. The Scheduler
If you stick to the "SimmateExecutor", then you're already all good to go! Nothing needs to be done. This is because the queue of job submissions is really just a database table inside the simmate database. Workers will queue this table and grab the first result.

## 2. Connecting to a Cloud Database
We learned from previous tutorials that simmate (by default) writes results to a local file named `~/simmate/my_env-database.sqlite3`. We also learned that cloud databases let many different computers share data and access the database through an internet connection. Because SQLite3 (the default database engine) is not build for hundreds of connections and we often use separate computers to run workflows, you should build a cloud database. Therefore, don't skip tutorial 08 where we set up a cloud database!

## 3. Connecting to the Scheduler
Because we are using the "SimmateExecutor" all we need is a connection to the cloud database. All you need to do make sure ALL of your computational resources are connected to the cloud database you configured. If your workers aren't picking up any of your workflow submissions, it's probably because you didn't connect them properly.

## 4. Connecting custom projects

If you have custom database tables or code, it's important that (a) the cloud database knows about these tables and (b) your remote resources can access your custom code. Therefore, your custom project/app should be installed and accessible by all of your computation resources. Be sure to `pip install your-cool-project` for all computers.

!!! tip
    Because SimmateExecutor uses cloudpickle when submitting tasks, many custom workflows will work just fine without this step. Our team is still working out how to guide users and make this as easy as possible. For now, we suggest just trying out your workflow when you skip this step -- as most times it will work. If not, then the text above explains why.
