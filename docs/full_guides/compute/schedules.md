# Schedules & Periodic Tasks

In addition to one-off workflows, Simmate supports **periodic tasks** (schedules). These are useful for:

- Regularly syncing data from third-party databases.
- Performing weekly database maintenance.
- Running "steady-state" evolutionary searches.

## Starting the Scheduler

Simmate uses a single "scheduler" process to manage all periodic tasks. You only need to run one of these for your entire project.

```bash
simmate compute start-schedules
```

The scheduler process will:

1. Search through all your installed apps for a `schedules.py` module.
2. Register any tasks defined in those modules.
3. Submit them to the queue database as `WorkItem`s at their specified intervals.

Because the scheduler process simply delegates tasks by creating `WorkItem`s, it never blocks. The actual execution of these tasks is picked up and handled asynchronously by your active Simmate Workers.

---

## Creating a Schedule

To add a schedule to your own app, create a `schedules.py` file in your app directory and use the built-in `@schedule` decorator.

```python
# my_app/schedules.py
from simmate.compute import schedule
from my_app.workflows import MyMaintenanceWorkflow

# Run every day at 10:30am
@schedule(interval="daily", at="10:30")
def run_daily_maintenance():
    MyMaintenanceWorkflow.run()

# Run every hour
@schedule(interval="hourly")
def check_for_updates():
    print("Checking for updates...")

# Run every Saturday at 1:00am
@schedule(interval="weekly", on="saturday", at="01:00")
def run_weekly_cleanup():
    print("Running weekly cleanup...")
```

As long as `my_app` is in your `settings.yaml` under `apps`, the `start-schedules` command will find and register these tasks automatically.

---

## Best Practices

- **Workers Required:** Since the `SimmateScheduler` does not run the tasks itself, you must ensure you have at least one worker running (`simmate compute start-worker`) to process the scheduled jobs from the database queue.
- **Task Delegation:** Decorating a task ensures that whenever the schedule interval hits, the scheduler submits the job directly as a `WorkItem`. Heavy lifting is naturally offloaded, preventing the scheduler loop from ever clogging.
