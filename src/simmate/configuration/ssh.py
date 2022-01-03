# -*- coding: utf-8 -*-

from fabric import Connection


class SSHConnection(Connection):
    """
    This is a utility for running python code through a remote ssh terminal. It
    was design specifically to make Spyder's remote kernal connection easier.

    Read more here:
        http://docs.spyder-ide.org/current/panes/ipythonconsole.html?highlight=ssh#connect-to-a-remote-kernel


    Usage
    ------

    Start by setting up your desired connection (replacing the example connection
    info with your own):

    .. code-block:: python
        from simmate.configuration.ssh import SSHConnection

        connection = SSHConnection(
            host="warwulf.net",
            user="WarrenLab",
            port=22,
            connect_kwargs={"password": "xxxxxx"},
            conda_env="test",
            working_directory="/media/synology/user/jack/debug/",
        )

    Note, SSHConnection inherits from fabric.Connection so it will accept the
    same type of connect_kwargs for improve security.

    When this code is ran, you can start a remote python kernal with...

    .. code-block:: python
        connection.start_remote_kernel()

    Leave this running throughout your session, and in a new Spyder console,
    run the follow code:

    .. code-block:: python

        from simmate.configuration.ssh import SSHConnection

        # This is the same connection object as before, but we need to run this
        # again because it's a new python console
        connection = SSHConnection(
            host="warwulf.net",
            user="WarrenLab",
            port=22,
            connect_kwargs={"password": "xxxxxx"},
            conda_env="test",
            working_directory="/media/synology/user/jack/debug/",
        )

        # and load the connection file to your computer
        connection.get_kernel_connection_file()

    Once you have the connect file, you can close this 2nd terminal -- but leave
    the first terminal open (where start_remote_kernel() is still running).

    You can then start a new terminal by selecting "Connect to an existing kernal"
    in Spyder, which will connect to the remote process that you started. To confirm
    everything is set up and working, run the following in your new terminal:

    .. code-block:: python

        # makes sure you're running code remotely. The output should be the
        # working directory of your remote computer
        import os
        os.getcwd()

        # makes sure you have simmate installed on your remote computer
        import simmate

    """

    def __init__(self, conda_env: str, working_directory: str = ".", **kwargs):

        # inherit from parent Connection class
        super().__init__(**kwargs)

        # and add the extra attributes
        self.conda_env = conda_env
        self.working_directory = working_directory

    def start_remote_kernel(self):
        """
        This functions starts a python kernal using the supplied anaconda
        environment and working directory. Note, this will run endlessly until
        you manually close the python console.
        """

        print(
            "DEAR SIMMATE USER: Be aware that this method will run endlessly until \n"
            "you close your Spyder console. The output below is from calling an \n"
            "external program and you will NOT be able to stop it with Crtl+\\. \n"
            "Instead, you MUST close the console manually in Spyder. \n\n\n"
        )

        # switch into the working directory
        with self.cd(self.working_directory):
            # and establish the correct conda env before running any command
            with self.prefix(f"source activate {self.conda_env}"):

                # BUG: How can I exit this without closing the terminal?
                # It would be nice if this ran in the background...
                # I'm unable to have this run in the background with "&" and don't
                # want to detach the the process, as it will run endlessly.
                # https://www.fabfile.org/faq.html#why-can-t-i-run-programs-in-the-background-with-it-makes-fabric-hang
                self.run("python -m spyder_kernels.console")

    def get_kernel_connection_file(self, filename: str):
        """
        Downloads the kernal connection file from the remote ssh computer to the
        current working directory.

        Parameters
        ----------
        filename : str
            The json filename given by the start_remote_kernel() method. It should
            be something like "kernel-123456.json"
        """

        # So the user makes sense of what's printed by the next command
        print("Copying connection from the following remote directory:")

        # and establish the correct conda env before running any command
        with self.prefix(f"source activate {self.conda_env}"):
            # grab the directory which holds all kernel json files
            directory = self.run("jupyter --runtime-dir").stdout.strip()
        # We can't use os.path.join here because we may be running this on Windows
        # when really want os.path.join to act like the remote computer.
        # BUG: for now, we assume the remote computer is Linux.
        connection_file = directory + f"/{filename}"

        result = self.get(connection_file)

        print(f"Success! You will find your connection file at:\n {result.local}")
