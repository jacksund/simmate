import os
import signal
import threading
from contextlib import contextmanager
from pathlib import Path

import psutil


@contextmanager
def handle_sigterm():
    """
    Converts SIGTERM into a `KeyboardInterrupt` so that it is handled the same
    way as crtl+c (SIGINT).

    This is needed in containers (docker, k8s) because they stop processes
    with SIGTERM. Python does not handle SIGTERM by default, and when running
    as PID 1 in a container, the signal is ignored entirely -- meaning the
    process is eventually force-killed (SIGKILL) without any clean up.

    The handler is only installed when called from the main thread, as python
    only allows signal handlers to be set there. The original handler is
    restored on exit.
    """
    if threading.current_thread() is not threading.main_thread():
        yield
        return

    def _raise_interrupt(signum, frame):
        # ignore any repeated SIGTERMs so they don't interrupt our clean up
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        raise KeyboardInterrupt("SIGTERM received")

    original_handler = signal.signal(signal.SIGTERM, _raise_interrupt)
    try:
        yield
    finally:
        signal.signal(signal.SIGTERM, original_handler)


def get_available_resources() -> tuple[float, float]:
    """
    Detects the CPU cores and RAM that this process is allowed to use.

    This accounts for:

    - CPU affinity (e.g. cores pinned by SLURM or `taskset`)
    - cgroup v2 limits (e.g. k8s pod limits, `docker run --cpus/--memory`, or
      SLURM jobs on cgroup v2 clusters)

    When no limits are set, the machine's totals are returned. This means that
    several workers sharing one machine without limits will each report the
    full machine. cgroup v1 limits (common on older HPC clusters) are not
    detected either.

    Returns:
        The number of CPU cores (which can be fractional, e.g. 1.5 for a
        k8s limit of "1500m") and the RAM in GB.
    """
    ncores = float(os.process_cpu_count() or 1)
    ram = psutil.virtual_memory().total

    # cgroup v2 lists this process's cgroup as a single "0::<path>" line. Limits
    # can be set on any parent cgroup too (e.g. on a SLURM job rather than its
    # step), so we check each level up to the root and keep the tightest. In
    # containers, the path is usually "/" so only the root is checked.
    # (there is no /proc on Mac or Windows, so they keep the machine totals)
    cgroup_file = Path("/proc/self/cgroup")
    lines = cgroup_file.read_text().splitlines() if cgroup_file.exists() else []
    for line in lines:
        if not line.startswith("0::"):
            continue
        relative = Path(line[3:].lstrip("/"))
        for path in [relative, *relative.parents]:
            folder = Path("/sys/fs/cgroup") / path
            # e.g. "150000 100000" for 1.5 cores, or "max 100000" for no limit
            cpu_file = folder / "cpu.max"
            if cpu_file.exists():
                quota, period = cpu_file.read_text().split()
                if quota != "max":
                    ncores = min(ncores, int(quota) / int(period))
            # in bytes, or "max" for no limit
            memory_file = folder / "memory.max"
            if memory_file.exists():
                limit = memory_file.read_text().strip()
                if limit != "max":
                    ram = min(ram, int(limit))

    return ncores, round(ram / 1024**3, 1)
