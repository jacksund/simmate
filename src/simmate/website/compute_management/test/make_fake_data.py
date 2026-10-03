# -*- coding: utf-8 -*-

"""
Generates `fake_data.zip`, which holds fake workers and work items for tests
and for exploring the compute dashboard (see `simmate dev load-test-data`).

Rerun this script whenever the compute models change. The output is
deterministic (fixed random seed), so the zip only changes when this script
does.

Every work item runs `time.sleep(1)`, so nothing harmful happens if a real
worker ever picks up one of the pending items.
"""

import random
import time
import uuid
from datetime import datetime, timedelta, timezone

import cloudpickle

from simmate.database import connect  # isort: skip

from simmate.database.utils import (  # isort: skip
    get_fake_data_path,
    get_fake_users,
    write_fake_data,
)

random.seed(1234)

REFERENCE_DATE = datetime(2026, 10, 1, 12, tzinfo=timezone.utc)
NOW = REFERENCE_DATE  # the loader shifts all dates so that this becomes "now"

LABEL = "compute_management"

users = get_fake_users()
user_ids = [u["id"] for u in users]

# -----------------------------------------------------------------------------

# (workflow name, queue tag, typical run time in hours, error rate)
WORKFLOWS = [
    ("relaxation.vasp.matproj", "vasp", 2, 0.05),
    ("static-energy.vasp.matproj", "vasp", 0.5, 0.03),
    ("electronic-structure.vasp.matproj-full", "vasp", 4, 0.10),
    ("population-analysis.vasp-bader.bader-matproj", "vasp", 1, 0.08),
    ("diffusion.vasp.neb-all-paths-mit", "vasp", 12, 0.20),
    ("relaxation.quantum-espresso.quality00", "qe", 1, 0.05),
    ("pka.schrodinger.jaguar-pka", "jaguar", 3, 0.10),
]

# Each "slot" is a machine that runs a series of workers (e.g. SLURM jobs that
# are resubmitted). (computer system, queue tag, ncores, ram, final status)
# where the final status is for the most recent worker in that slot.
SLOTS = [
    ("hpc-node-01", "vasp", 64, 256, "Running"),
    ("hpc-node-02", "vasp", 64, 256, "Running"),
    ("hpc-node-03", "vasp", 64, 256, "Idle"),
    ("hpc-node-04", "vasp", 64, 256, "Stale"),
    ("lab-workstation", "qe", 16, 64, "Idle"),
    ("hpc-node-05", "qe", 32, 128, "Stale"),
    ("gpu-node-01", "jaguar", 32, 128, "Stopped"),
]

FXN = cloudpickle.dumps(time.sleep)
ARGS = cloudpickle.dumps([1])
KWARGS = cloudpickle.dumps({})

ERRORS = [
    "NonConvergingError: The electronic structure failed to converge after 3 attempts",
    "TimeoutError: Calculation exceeded the walltime of 24 hours",
    "FileNotFoundError: OUTCAR was not created",
    "MemoryError: Unable to allocate 12.4 GiB for an array",
    "Exception: ZBRENT: fatal error in bracketing",
]


def random_uuid() -> uuid.UUID:
    return uuid.UUID(int=random.getrandbits(128), version=4)


# -----------------------------------------------------------------------------

# Build a series of back-to-back workers for each slot over the last 30 days.
# Workers get private "_start", "_end", and "_busy_until" keys that are
# removed before writing.
workers = []
for system, queue, ncores, ram, final_status in SLOTS:
    until = NOW - timedelta(days=7) if final_status == "Stopped" else NOW
    start = NOW - timedelta(days=random.uniform(25, 30))
    while True:
        end = min(start + timedelta(days=random.uniform(1, 5)), until)
        worker = dict(
            id=len(workers) + 1,
            created_at=start,
            status="Stopped",
            owner_id=random.choice(user_ids),
            ncores=ncores,
            ram=ram,
            computer_system=system,
            directory=f"/scratch/simmate/worker-{len(workers) + 1:03d}",
            tags=[queue],
            nitems_max=None,
            timeout=None,
            close_on_empty_queue=False,
            waittime_on_empty_queue=15,
            _start=start,
            _end=end,
            _busy_until=start,
        )
        workers.append(worker)
        if end < until:
            if random.random() < 0.1:
                worker["status"] = "Crashed"
            # gap while the next job waits in the SLURM queue
            start = end + timedelta(hours=random.uniform(0.1, 6))
            continue
        if final_status == "Stale":
            # still claims to be running but stopped checking in
            worker["status"] = "Running"
            worker["_end"] = max(
                NOW - timedelta(minutes=random.uniform(20, 180)),
                start + timedelta(hours=1),
            )
        elif final_status != "Stopped":
            worker["status"] = final_status
            worker["_end"] = NOW - timedelta(seconds=random.uniform(5, 50))
        break


def find_worker(queue: str, at: datetime) -> tuple[dict, datetime] | None:
    """
    Gives the worker that would pick up an item submitted at the given time,
    and when it starts the item (once the worker is free).
    """
    options = [w for w in workers if queue in w["tags"] and w["_start"] <= at]
    for worker in sorted(options, key=lambda w: w["_busy_until"]):
        started_at = max(at, worker["_busy_until"])
        started_at += timedelta(seconds=random.uniform(5, 60))
        if started_at < worker["_end"]:
            return worker, started_at
    return None


# -----------------------------------------------------------------------------

work_items = []


def add_item(workflow: tuple, created_at: datetime, **kwargs):
    name, queue, *_ = workflow
    item = dict(
        id=random_uuid(),
        created_at=created_at,
        updated_at=created_at,
        tags=[queue, name],
        status="P",
        fxn=FXN,
        args=ARGS,
        kwargs=KWARGS,
        result_binary=None,
        worker_id=None,
        started_at=None,
    )
    item.update(kwargs)
    work_items.append(item)
    return item


# Past items, which are denser recently. Some workflows have a recent spike in
# errors so that the dashboard has something to flag.
for created_at in sorted(
    NOW - timedelta(days=min(random.expovariate(1 / 7), 30)) for _ in range(550)
):
    workflow = random.choice(WORKFLOWS)
    name, queue, hours, error_rate = workflow

    match = find_worker(queue, created_at)
    if not match:
        if NOW - created_at > timedelta(hours=6):
            # nobody picked it up, so someone cancelled it
            add_item(workflow, created_at, status="C", updated_at=created_at + timedelta(hours=6))  # fmt: skip
        continue
    worker, started_at = match

    finished_at = started_at + timedelta(hours=hours * random.uniform(0.3, 2))
    if finished_at > worker["_end"]:
        continue  # would still be running (a few of these are added below)
    worker["_busy_until"] = finished_at

    if NOW - created_at < timedelta(days=1) and queue == "vasp":
        error_rate *= 4
    is_error = random.random() < error_rate
    add_item(
        workflow,
        created_at,
        status="E" if is_error else "F",
        started_at=started_at,
        updated_at=finished_at,
        worker_id=worker["id"],
        result_binary=cloudpickle.dumps(
            Exception(random.choice(ERRORS)) if is_error else None
        ),
    )

# Items that are running now. This includes some on stale workers (which are
# "orphaned") and one that has been running for over a day.
for worker in workers:
    if worker["status"] == "Running":
        workflow = random.choice([w for w in WORKFLOWS if w[1] in worker["tags"]])
        started_at = max(
            worker["_busy_until"],
            worker["_end"] - timedelta(hours=random.uniform(0.2, 3)),
        )
        add_item(
            workflow,
            started_at - timedelta(minutes=random.uniform(1, 30)),
            status="R",
            started_at=started_at,
            updated_at=started_at,
            worker_id=worker["id"],
        )
long_item = next(i for i in work_items if i["status"] == "R")
long_item["started_at"] = long_item["updated_at"] = NOW - timedelta(hours=30)
long_item["created_at"] = NOW - timedelta(hours=31)

# Items waiting in the queue. The "jaguar" queue has no active workers.
for _ in range(25):
    add_item(
        random.choice(WORKFLOWS),
        NOW - timedelta(hours=random.expovariate(1 / 3)),
    )

work_items.sort(key=lambda i: i["created_at"])

# -----------------------------------------------------------------------------

for worker in workers:
    items = [i for i in work_items if i["worker_id"] == worker["id"]]
    done = [i for i in items if i["status"] in ("F", "E")]
    up_time = (worker["_end"] - worker["_start"]).total_seconds()
    workflow_time = sum(
        (i["updated_at"] - i["started_at"]).total_seconds() for i in done
    )
    worker.update(
        updated_at=worker.pop("_end"),
        nitems_completed=len(done),
        total_up_time=up_time,
        total_workflow_time=workflow_time,
        idle_percent=round(100 * (1 - workflow_time / up_time), 1),
    )
    del worker["_start"], worker["_busy_until"]

# -----------------------------------------------------------------------------

write_fake_data(
    filename=get_fake_data_path(LABEL),
    tables={
        "auth.User": users,
        f"{LABEL}.SimmateWorker": workers,
        f"{LABEL}.WorkItem": work_items,
    },
    reference_date=REFERENCE_DATE,
)
