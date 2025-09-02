# -*- coding: utf-8 -*-

from pathlib import Path

import paramiko


class SshServer:
    """
    A simple wrapper around paramiko's shh/sftp client

    Having this as a wrapper lets us add utility methods for common actions on
    a given SSH server (such as an HPC cluster).

    Original paramiko objects can also be used by using the `client` property,
    which returns a `paramiko.SSHClient` object.
    """

    host: str = None
    user: str = None
    password: str = None

    # OPTIMIZE: Should I cache this...?
    @classmethod
    @property
    def client(cls):

        if not cls.host or not cls.user or not cls.password:
            raise Exception(
                "A host, user, and password must be set for a SshServer class"
            )

        ssh = paramiko.SSHClient()

        # make sure we can ssh to the host if the key doesn't exist yet
        ssh.load_system_host_keys()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy)

        ssh.connect(
            hostname=cls.host,
            username=cls.user,
            password=cls.password,
        )

        return ssh

    @classmethod
    def copy_local_to_remote(cls, local: str | Path, remote: str | Path) -> Path:
        with cls.client.open_sftp() as sftp_client:
            sftp_client.put(
                remotepath=str(remote),
                localpath=str(local),
            )
        return Path(remote)

    @classmethod
    def copy_remote_to_local(cls, local: str | Path, remote: str | Path) -> Path:
        with cls.client.open_sftp() as sftp_client:
            sftp_client.get(
                remotepath=str(remote),
                localpath=str(local),
            )
        return Path(local)

    @classmethod
    def call_command_remote(cls, command: str) -> str:
        ssh_stdin, ssh_stdout, ssh_stderr = cls.client.exec_command(command)
        # TODO: do I want to just return stdout? Raise an error if there is one?
        return ssh_stdout.read()

    # TODO:
    #   copy many files (rather than new sftp each file)
    #   read file --> i.e. copy, read content, and then delete
