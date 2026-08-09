# Monitoring & Cleanup

Simmate provides several CLI commands to monitor the status of your queue and manage WorkItems. These commands are essential for keeping track of large batches of jobs and maintaining a healthy database.

## Checking Queue Stats

To get a quick overview of how many jobs are in each state (Pending, Running, Finished, Errored, Canceled), use:

```bash
simmate compute stats
```

For a more detailed breakdown, including stats for each specific workflow (categorized by tags), use:

```bash
simmate compute stats-detail
```

You can also filter these stats by time to see recent activity:

```bash
# Show stats for jobs updated in the last 24 hours
simmate compute stats-detail --recent 24
```

---

## Inspecting WorkItems

To see a list of individual jobs and their current status in a table format, use the `workitems` command:

```bash
simmate compute workitems
```

You can filter the list by status, tags, or recency:

```bash
# Show only errored jobs
simmate compute workitems --status E

# Show jobs with a specific tag
simmate compute workitems --tag my-tag

# Show jobs updated in the last 12 hours
simmate compute workitems --recent 12
```

---

## Error Summaries

When jobs fail, they are marked as `Errored` (E). To see a quick summary of the error messages for all failed jobs without digging into individual log files, run:

```bash
simmate compute error-summary
```

This command will print the WorkItem ID followed by the exception message, making it easy to identify common failure modes across your cluster.

---

## Cleaning Up the Queue

Over time, the `WorkItem` table can grow very large, which may eventually slow down database queries. It's a good practice to periodically delete old or unnecessary entries.

!!! warning
    All `delete` commands require the `--confirm` flag to execute.

### Deleting Finished Jobs
This is the most common cleanup task. It removes entries for jobs that completed successfully.

```bash
simmate compute delete-finished --confirm
```

### Deleting by Tag
If you ran a test batch or a specific project that is now complete, you can delete those specific entries:

```bash
simmate compute delete --tag test-runs --confirm
```

!!! note
    If you run `simmate compute delete --confirm` without any tags, it will delete all jobs that have **no** tags assigned to them.

### Deleting Everything
!!! danger
    This will delete **ALL** jobs from the queue, including those that are currently `Pending` or `Running`. Use this with caution.

```bash
simmate compute delete-all --confirm
```

---

## Programmatic Monitoring

If you are using Python, you can monitor and manage jobs directly using the `WorkItem` object returned by `run_cloud()`:

- `workitem.is_done()`: Returns `True` if the job finished or was canceled.
- `workitem.is_running()`: Returns `True` if a worker is currently processing the job.
- `workitem.is_pending()`: Returns `True` if the job is still in the queue.
- `workitem.cancel()`: Attempts to cancel a `Pending` job.
- `workitem.result()`: A **blocking** call that waits for the job to finish and returns the result.


---

## Database Maintenance

If you are using a shared Postgres database, the WorkItem table is often the most frequently updated table. In addition to deleting entries via Simmate, you may occasionally need to run standard database maintenance commands like `VACUUM` (in Postgres) to reclaim disk space after large deletions.
