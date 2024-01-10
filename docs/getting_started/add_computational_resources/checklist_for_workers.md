# Worker Setup Checklist

Now that you're familiar with the terms **scheduler**, **cluster**, and **worker**, let's walk through the checklist to set everything up:

- [x] Configure your scheduler
- [x] Connect a cloud database
- [x] Establish a connection to the scheduler
- [x] Register all custom projects/apps

## 1. The Scheduler
If you're using the "SimmateExecutor", you're all set! No additional setup is required. This is because the job submission queue is essentially a database table within the simmate database. Workers will queue this table and pick up the first result.

## 2. Connecting to a Cloud Database
As we've learned from previous tutorials, simmate, by default, writes results to a local file named `~/simmate/my_env-database.sqlite3`. Cloud databases, on the other hand, allow multiple computers to share data and access the database via an internet connection. Since SQLite3 (the default database engine) isn't designed for hundreds of connections and we often use separate computers to run workflows, it's advisable to set up a cloud database. Don't miss tutorial 08 where we guide you through this process!

## 3. Connecting to the Scheduler
With the "SimmateExecutor", all you need is a connection to the cloud database. Ensure that ALL your computational resources are connected to the configured cloud database. If your workers aren't picking up any workflow submissions, it's likely due to an improper connection.

## 4. Connecting Custom Projects

If you have custom database tables or code, it's crucial that (a) the cloud database is aware of these tables and (b) your remote resources can access your custom code. Therefore, your custom project/app should be installed and accessible on all your computation resources. Remember to `pip install your-cool-project` on all computers.

!!! tip
    The SimmateExecutor uses cloudpickle when submitting tasks, so many custom workflows will function without this step. We're still figuring out the best way to guide users through this process. For now, we recommend testing your workflow even if you skip this step -- it often works. If it doesn't, the above text explains why.