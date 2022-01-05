# -*- coding: utf-8 -*-

import os
import time

from fabric import Connection

# BUG: This class is currently broken because Spyder needs to use a jump-host
# in order to connect with the batch-job process.
# ssh -J WarrenLab@warwulf.net WarrenLab@c18
# see https://github.com/spyder-ide/spyder-kernels/issues/359


class SSHConnection(Connection):
    """
    This is a utility for running python code through a remote ssh terminal and
    a PBS/SLURM job queue. It was designed specifically to make Spyder's remote
    kernal connection easier for beginners.

    Read more here:
        http://docs.spyder-ide.org/current/panes/ipythonconsole.html?highlight=ssh#connect-to-a-remote-kernel


    Usage Guide
    ------------

    This class's use is comprised of the following steps:

        1. set up your ssh host, username, and password settings
        2. call setup_remote_kernal and wait for resources to be granted
        3. start a new terminal in Spyder with the connection json file supplied

    Steps 1-2 are completed with the following code, which includes example
    SSH connection settings and SLURM submission command (so be sure to update these):

    .. code-block:: python
        from simmate.configuration.ssh import SSHConnection

        # Example here uses SLURM (sbatch) to submit a job limted to 1 hour.
        # We HIGHLY recommend setting a time limit below 3 hrs to avoid hogging
        # resources outside of your interactive session.
        # This command below is the same as submitting a script with...
        #
        # #SBATCH --nodes=1
        # #SBATCH --ntasks=2
        # #SBATCH --cpus-per-task 1
        # #SBATCH --mem=4GB
        # #SBATCH --partition=p1
        # #SBATCH --time=03:00:00
        #

        # set up the connection
        connection = SSHConnection(
            host="warwulf.net",
            user="WarrenLab",
            connect_kwargs={"password": "xxxxxx"},
            conda_env="test",
            working_directory="/media/synology/user/jack/debug",  # no ending slash!
            submit_command="sbatch -N 1 -n 2 -c 1 --mem=4GB -p p1 -t 03:00:00",
        )

        # Submit your SLURM job, which creates the remote python kernal for you.
        # It will also wait for the job to start, and copy the connection file
        # over to your computer
        connection.setup_remote_kernel()

    Make note of the connection file that is printed out. Once you have this,
    you're all done with this terminal and can close it!

    You can then start a new terminal by selecting "Connect to an existing kernal"
    in Spyder and use the file that is printed out above. This will connect to the
    remote process that you started. To confirm everything is set up and working,
    run the following in your new terminal:

    .. code-block:: python

        # makes sure you're running code remotely. The output should be the
        # working directory of your remote computer
        import os
        os.getcwd()

        # makes sure you have simmate installed on your remote computer
        # if this fails, you need to make sure an environment with Simmate install
        # on your remote computer in addition to your local computer.
        import simmate

    One important thing to remember is that your submitted job will NOT be
    canceled automatically when you close Spyder or your python terminal. Be
    sure to cancel the job when you're done. This is done by typing "exit" in
    your new python terminal.

    """

    def __init__(
        self,
        conda_env: str,
        submit_command: str,
        working_directory: str = ".",
        port: int = 22,  # indicates we are using SSH
        **kwargs,
    ):
        """
        Creates a fabric.Connection where a remote python kernal can be easily
        set up and connected to through SLURM.

        Parameters
        ----------
        conda_env : str
            The conda environment to start with python kernal with. Note, this
            environment is only used within start_remote_kernel() and will not
            be used by the run() method.
        submit_command : str
            The command used to submit to a SLURM or PBS queue system. This should
            be something like "sbatch -N 1 -n 2 -c 2 -p p1 -t 03:00:00" for SLURM.
            PBS is also supported (although not tested in production).
        working_directory : str, optional
            The directory to start the python kernal in. Note, this
            directory is only used within start_remote_kernel() and will not
            be used by the run() method. The default is "." which is the home
            directory.
        port: int
            the remote port. Defaults to 22, which is an SSH connection.
        **kwargs :
            Any arguments passed to fabric.Connection.
        """

        # inherit from parent Connection class
        super().__init__(port=port, **kwargs)

        # and add the extra attributes
        self.conda_env = conda_env
        self.working_directory = working_directory
        self.submit_command = submit_command

        # Warn the user about how PBS has not been tested
        if submit_command.startswith("qsub"):
            raise Exception(
                "This class has not been tested with PBS. If you have a cluster "
                "that we can test with, please reach out to our team and we can "
                "can implement this feature!"
            )

        # We assume the output file for SLURM so stop the user if they tried
        # overwriting this.
        if submit_command.startswith("sbatch") and any(
            x in submit_command for x in ["-o ", "--output "]
        ):
            raise Exception(
                "For this class to work properly, please do not specify the output "
                "filename. If this is a problem for your team, let our team know!"
            )

    def start_remote_kernel(self, sleep_step: int = 3):
        """
        Completes the following steps:
            1. Submit job to cluster which will create a python kernel
            2. Waits for the SLURM/PBS job to start
            3. Loads the connection filename from the batch job output file
            4. Copies the connection file to the local computer

        Parameters
        ----------
        sleep_step : int, optional
            Time to wait between checking if the batch job started. The default
            is 3 seconds.
        """

        # -------------------------------------------------

        # STEP 1: Submit job to cluster

        print("Submitting job to remote cluster...")

        # switch into the working directory
        with self.cd(self.working_directory):
            # and establish the correct conda env before running any command
            with self.prefix(f"source activate {self.conda_env}"):

                # This command starts a python kernel that runs endlessly
                kernel_command = "python -m spyder_kernels.console"

                # How we submit this kernel_command to SLURM/PBS depends on which
                # queue system we are using.
                # SLURM uses "sbatch ... --wrap ..."
                if self.submit_command.startswith("sbatch"):
                    output = self.run(
                        f"{self.submit_command} --wrap '{kernel_command}'"
                    )
                    # The job id is the at the end of the line for output
                    job_id = output.stdout.strip().split()[-1]

                # PBS uses "qsub ... -- ..."
                # elif self.submit_command.startswith("qsub"):
                #     self.run(f"{self.submit_command} -- {kernel_command}")
                # Other systems aren't supported yet and should raise an error.
                else:
                    raise Exception(
                        "The submit_command you provided doesn't match SLURM or "
                        " PBS foramts. SLURM should use sbatch, and PBS should use qsub."
                    )

        # -------------------------------------------------

        # STEP 2: wait for the SLURM/PBS job to start

        print("Waiting for batch job to start...")

        # the slurm output will be named something like /path/to/dir/slurm-12345.out
        # We can't use os.path.join here because we may be running this on Windows
        # when really want os.path.join to act like the remote computer.
        # BUG: for now, we assume the remote computer is Linux.
        if self.submit_command.startswith("sbatch"):
            output_filename = self.working_directory + f"/slurm-{job_id}.out"
        else:
            raise Exception(
                "The submit_command you provided doesn't match SLURM or "
                " PBS foramts. SLURM should use sbatch, and PBS should use qsub."
            )

        # We simply wait until an output file shows up, and once it does, we know
        # that the job has started.
        print(f"Watching for file to exist: {output_filename}")
        while True:
            # check if the output file was written yet
            if not self.run(f"test -f {output_filename}", warn=True).failed:
                break
            # if not, sleep for X seconds until checking again
            time.sleep(sleep_step)

        # Once we know the file exists, we still want to wait 3 extra seconds to
        # give our kernel time to setup. This avoids a race condition.
        time.sleep(3)

        print("Job has started.")

        # -------------------------------------------------

        # STEP 3: Load the connection filename from the batch job output file

        print("Loading connection file location...")

        # transfer the file to the local desktop and grab the filename
        output_filename_local = self.get(output_filename).local

        # Read the file contents for the json connection filename, which will
        # be at the very end of the file.
        with open(output_filename_local) as output_file:
            lines = output_file.readlines()
            connection_filename = lines[-1].split()[-1]
        # we are done with this file so we can delete it
        os.remove(output_filename_local)

        # and establish the correct conda env before running any command
        with self.prefix(f"source activate {self.conda_env}"):
            # grab the directory which holds all kernel json files
            directory = self.run("jupyter --runtime-dir").stdout.strip()
        # We can't use os.path.join here because we may be running this on Windows
        # when really want os.path.join to act like the remote computer.
        # BUG: for now, we assume the remote computer is Linux.
        connection_filename_full = directory + f"/{connection_filename}"

        # -------------------------------------------------

        # STEP 4: Copy the connection file to the local computer

        print("Transfering connection file to local computer...")

        result = self.get(connection_filename_full)

        print(
            f"\n\nSuccess! You will find your connection file at:\n {result.local}\n\n"
        )
        print(
            "Up next, go to Spyder > Console options (bottom right) > Connect to "
            "an Existing Kernal. You can close this console whenever.\n"
            "NOTE: when you are done with your remote kernal, type 'exit' in your "
            "new console so that the kernel (and batch job) are terminated."
        )
