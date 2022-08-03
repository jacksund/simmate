# -*- coding: utf-8 -*-

import os
import time
import datetime
import subprocess

import numpy
from pymatgen.io.vasp.outputs import Outcar

from simmate.workflow_engine import ErrorHandler
from simmate.calculators.vasp.error_handlers import Unconverged


class Walltime(ErrorHandler):
    """
    Checks if a run is nearing the walltime of a SLURM job that it's
    running in. If so, VASP can be stopped by writing a STOPCAR with
    LSTOP or LABORT = True.

    Walltime is detected automatically based on environment variables set by
    SLURM, so if no variable is detected, this error handler has no effect.

    Support for PBS and other queue systems is not yet supported.

    For a similar implementation, see the `WallTimeHandler` in custodian located
    [here](https://github.com/materialsproject/custodian/blob/048adec8c965c1a01d69ac8294f039638941df74/custodian/vasp/handlers.py#L1521-L1629)
    """

    is_monitor = True
    has_custom_termination = True

    def __init__(
        self,
        wall_time: float = None,
        buffer_time: float = 900,  # 15 min
        electronic_step_stop: bool = False,
    ):
        """
        Initializes the handler with a buffer time.

        #### Parameters

        - `wall_time`:
            Total walltime for the calculation (in seconds). If this is None,
            and the job is running on a job-queue system, the handler will
            attempt to determine the remaining time using environment variables.
            If the wall time cannot be determined or is not set, this error
            handler will have no effect.

        - `buffer_time`:
            The minimum amount of time remaining to trigger this error handler.
            This is important because this error handler is only called
            periodically (e.g. once every 5 min). Therefore, if less than this
            buffer time remains, the error might not be caught because there
            won't be another check. When setting this, the S3Task's
            monitor_freq, polling_timestep, and time it takes to run all the
            other error handlers.

        - `electronic_step_stop`:
            Whether to check for electronic steps instead of ionic steps
            (e.g. for static runs on large systems or static HSE runs, ...).
            Be careful that results such as density or wavefunctions might
            not be converged at the electronic level. Should be used with
            LWAVE = .True. to be useful. If this is True, the STOPCAR is
            written with LABORT = .TRUE. instead of LSTOP = .TRUE.
        """
        self.wall_time = wall_time
        self.buffer_time = buffer_time
        self.electronic_step_stop = electronic_step_stop

    def check(self, directory: str) -> bool:
        """
        Check for error.
        """

        remaining_time = self._get_remaining_time(directory)

        # None means we ignore this error handler
        if remaining_time == None:
            return False

        # If the remaining time is less than our buffer time or time for 2
        # steps, then we also want to begin shutdown out of caution.
        time_per_step = self._get_max_step_time(directory)

        if (remaining_time < self.buffer_time) or (remaining_time < time_per_step * 2):
            # make sure the calculation didn't "finish at the buzzer"
            is_finished = self._check_if_finished(directory)
            if is_finished:
                print(
                    "BUZZER BEATER!!! This job finished right when it was "
                    "about to hit the walltime!"
                )
                return False
            # BUG: there may be a rare race condition here where the job completes
            # in the time it takes to indicate this check

            return True

        # Otherwise we don't have this error.
        return False

    def terminate_job(self, directory: str, **kwargs) -> bool:
        """
        When a walltime is about to be hit, we want to tell VASP to end
        naturally by creating a STOPCAR file. We do not want to allow and
        new VASP attempts, so we return a value of False for allow_retry
        """

        stopcar_filename = os.path.join(directory, "STOPCAR")
        stopcar_content = (
            "LSTOP = .TRUE." if not self.electronic_step_stop else "LABORT = .TRUE."
        )

        with open(stopcar_filename, "w") as stopcar:
            stopcar.write(stopcar_content)

        return False

    def correct(self):
        raise Exception("Stopped job due to Walltime limit.")
        # return "Added STOPCAR file to end job"  # ... and resubmitted

    def _get_remaining_time(self, directory: str) -> float:
        """
        Detects the amount of time remaining for a job by looking for class
        settings (e.g. wall_time), environment variables, or looking at file
        timestamps.

        Returns `None` if unable to detect the remaining time.
        """

        # A explicitly given wall time takes priority
        if self.wall_time:
            # check the remaining time by looking at the timestamp of the
            # simmate_metadata.yaml.
            # If there is no simmate_metadata.yaml (meaning the S3task
            # was ran outside of a Workflow), then we say that wall_time cannot
            # be determined. (checking files like INCAR won't work bc of other
            # handlers updating them)
            filename = os.path.join(directory, "simmate_metadata.yaml")
            if not os.path.exists(filename):
                print("Unable to detect the time remaining. Ignoring Timeout.")
                return
                # !!! What if I looked at the creation time of the current directory?

            time_since_creation = time.time() - os.path.getmtime(filename)

            remaining_time = self.wall_time - time_since_creation

            return remaining_time

        # Next we see if we are in a SLURM environment
        elif "SLURM_JOBID" in os.environ:

            output = subprocess.run(
                "squeue -h -O TimeLeft -j $SLURM_JOBID",
                shell=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            # parse the output into a time
            if output == "INVALID":
                print(
                    "WARNING: SLURM node improperly configured. "
                    "Cannot detect TimeLeft"
                )
                return
            elif output == "UNLIMITED":
                return
            else:
                # OPTIMIZE: this section could benefit from regex.

                # Converts a string like "199-21:58:12" to ['199', '21', '58', '12']
                try:
                    output = [int(i) for i in output.replace("-", ":").split(":")]
                except:
                    print(
                        "Failed to parse SLURM output. Please report this to the"
                        f"Simmate team. Output was {output}"
                    )
                    return
                # this funky format is because we don't know how long our list
                # will be.
                time_inputs = {}
                if len(output) == 4:
                    time_inputs["days"] = output[-4]
                if len(output) >= 3:
                    time_inputs["hours"] = output[-3]
                if len(output) >= 2:
                    time_inputs["minutes"] = output[-2]
                if len(output) >= 1:
                    time_inputs["seconds"] = output[-1]

                remaining = datetime.timedelta(**time_inputs).total_seconds()
                return remaining

        # TODO:
        # For PBS, I could use PBS_WALLTIME but I don't have a PBS system to
        # implement and test this out.

        # If nothing was triggered above, we ignore this handler.
        else:
            return None

    def _get_max_step_time(self, directory: str) -> float:
        """
        Looks at completed ionic/electronic steps to see the maximum time
        for each new step. Whether ion or electronic step time is returned
        depends on the electronic_step_stop setting.
        """

        outcar_filename = os.path.join(directory, "OUTCAR")
        outcar = Outcar(outcar_filename)

        # NOTE: this code is copied from the custodian error handler and
        # I choose not to mess with the regex. Parsing of time steps could
        # be moved to the Outcar class though.

        # Determine max time per ionic step.
        if not self.electronic_step_stop:

            outcar.read_pattern(
                {"timings": r"LOOP\+.+real time(.+)"}, postprocess=float
            )
            time_per_step = (
                numpy.max(outcar.data.get("timings"))
                if outcar.data.get("timings", [])
                else 0
            )

        # Determine max time per electronic step.
        else:

            outcar.read_pattern({"timings": "LOOP:.+real time(.+)"}, postprocess=float)
            time_per_step = (
                numpy.max(outcar.data.get("timings"))
                if outcar.data.get("timings", [])
                else 0
            )

        return time_per_step

    def _check_if_finished(self, directory: str):
        # We can invert the unconverged check in order to see if the calc is done.
        return not Unconverged().check(directory)
        # BUG: Will this work properly for MD simulations? Should I check the
        # number of steps completed?
