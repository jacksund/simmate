# Schedules & Periodic Tasks

In addition to one-off workflows, Simmate supports **periodic tasks** (schedules). These are useful for:

- Regularly syncing data from third-party databases.
- Performing weekly database maintenance.
- Running "steady-state" evolutionary searches.

## Starting the Scheduler

Simmate uses a single "scheduler" process to manage all periodic tasks. You only need to run one of these for your entire project.

```bash
simmate engine start-schedules
```

The scheduler process will:

1. Search through all your installed apps for a `schedules.py` module.
2. Register any tasks defined in those modules.
3. Run them at their specified intervals.

---

## Creating a Schedule

To add a schedule to your own app, create a `schedules.py` file in your app directory. Simmate uses the [schedule](https://schedule.readthedocs.io/) library's syntax.

```python
# my_app/schedules.py
import schedule
from my_app.workflows import my_maintenance_workflow

# Run every day at 10:30am
schedule.every().day.at("10:30").do(my_maintenance_workflow.run)

# Run every hour
schedule.every().hour.do(my_maintenance_workflow.run)
```

As long as `my_app` is in your `settings.yaml` under `apps`, the `start-schedules` command will find and register these tasks.

---

## Best Practices

- **Avoid Long-Running Tasks:** The default `SimmateScheduler` runs tasks **sequentially**. If one task takes 5 hours to complete, it will block all other scheduled tasks until it finishes.
- **Use `run_cloud` for Heavy Lifting:** If your scheduled task is computationally expensive, have the schedule call `run_cloud()` instead of `run()`. This way, the scheduler just "submits" the job to the database queue and immediately moves on to the next schedule, while a worker handles the actual computation on a different machine.
