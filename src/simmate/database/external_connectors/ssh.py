# -*- coding: utf-8 -*-

from contextlib import contextmanager
from pathlib import Path, PurePosixPath
from stat import S_ISDIR

import paramiko
from rich.progress import track


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
    @contextmanager
    def _sftp_session(cls, sftp=None):
        """
        A context manager that yields an open `paramiko.SFTPClient`.

        Opening a session is expensive (a full SSH handshake), so methods that
        touch many files should open one session and reuse it. Passing an
        already-open client to `sftp` yields it back as-is and leaves it open,
        which is how the remote helpers below share a single session.
        """
        if sftp is not None:
            yield sftp
            return

        with cls.client as client:
            with client.open_sftp() as new_sftp:
                yield new_sftp

    @staticmethod
    def _to_remote_str(remote: str | Path) -> str:
        """
        Converts a remote path to a POSIX-style string, without any trailing
        slash (so that paths can be safely joined with f-strings).

        Remote paths are always POSIX, but this code can run on Windows, where
        `pathlib.Path` would build paths with backslashes. Never use `Path` for
        remote paths -- use this method (or `PurePosixPath`) instead.
        """
        remote = str(remote).replace("\\", "/")
        # the root dir ("/") is the one case where the trailing slash is kept
        return remote if remote == "/" else remote.rstrip("/")

    # -------------------------------------------------------------------------
    # Single-file + command helpers
    # -------------------------------------------------------------------------

    @classmethod
    def copy_local_to_remote(cls, local: str | Path, remote: str | Path) -> Path:
        with cls._sftp_session() as sftp:
            sftp.put(
                remotepath=cls._to_remote_str(remote),
                localpath=str(local),
            )
        return Path(remote)

    @classmethod
    def copy_remote_to_local(cls, local: str | Path, remote: str | Path) -> Path:
        with cls._sftp_session() as sftp:
            sftp.get(
                remotepath=cls._to_remote_str(remote),
                localpath=str(local),
            )
        return Path(local)

    @classmethod
    def call_command_remote(cls, command: str) -> str:
        with cls.client as client:
            ssh_stdin, ssh_stdout, ssh_stderr = client.exec_command(command)
            # TODO: do I want to just return stdout? Raise an error if there is one?
            return ssh_stdout.read()

    # -------------------------------------------------------------------------
    # Remote directory helpers
    #
    # These all accept an optional `sftp` client so that a caller can share one
    # session across many calls. See `_sftp_session` above.
    # -------------------------------------------------------------------------

    @classmethod
    def exists_remote(cls, remote: str | Path, sftp=None) -> bool:
        """
        Checks whether a remote file or directory exists.
        """
        with cls._sftp_session(sftp) as sftp:
            try:
                sftp.stat(cls._to_remote_str(remote))
                return True
            except FileNotFoundError:
                return False

    @classmethod
    def mkdir_remote(cls, remote: str | Path, sftp=None) -> str:
        """
        Creates a remote directory, including any missing parent directories.

        This is the equivalent of `mkdir -p` and is safe to call when the
        directory already exists.

        #### Parameters

        - `remote`:
            The remote directory to create.

        #### Returns

        - `remote`:
            The remote directory as a POSIX-style string.
        """
        remote = cls._to_remote_str(remote)
        remote_path = PurePosixPath(remote)

        # work from the top down, skipping the root (e.g. "/" or "."), which
        # always exists
        parents = [p for p in reversed(remote_path.parents) if str(p) not in ["/", "."]]

        with cls._sftp_session(sftp) as sftp:
            for directory in parents + [remote_path]:
                if cls.exists_remote(directory, sftp=sftp):
                    continue
                try:
                    sftp.mkdir(str(directory))
                except OSError:
                    # another process may have made it since the check above.
                    # This is only a true failure if it still isn't there.
                    if not cls.exists_remote(directory, sftp=sftp):
                        raise

        return remote

    @classmethod
    def listdir_remote(cls, remote: str | Path, sftp=None) -> dict:
        """
        Lists the immediate contents of a remote directory (one level deep),
        equivalent to running `ls` on it.

        #### Parameters

        - `remote`:
            The remote directory to inspect.

        #### Returns

        A dict with two keys, each holding a list of names (not full paths):
        - `"folders"`: subdirectories at this level
        - `"files"`: files at this level
        """
        with cls._sftp_session(sftp) as sftp:
            contents = sftp.listdir_attr(cls._to_remote_str(remote))
        return {
            "folders": [c.filename for c in contents if S_ISDIR(c.st_mode)],
            "files": [c.filename for c in contents if not S_ISDIR(c.st_mode)],
        }

    @classmethod
    def walk_remote(cls, remote: str | Path, sftp=None) -> list[str]:
        """
        Recursively lists all files within a remote directory.

        #### Parameters

        - `remote`:
            The remote directory to walk.

        #### Returns

        A list of POSIX-style file paths *relative* to `remote` (e.g.
        `["file1.txt", "subfolder/file2.txt"]`). Directories are not included.
        """
        remote = cls._to_remote_str(remote)

        with cls._sftp_session(sftp) as sftp:
            contents = cls.listdir_remote(remote, sftp=sftp)
            files = contents["files"]
            for folder in contents["folders"]:
                # recurse, then prefix the results with this subfolder's name
                subfiles = cls.walk_remote(f"{remote}/{folder}", sftp=sftp)
                files += [f"{folder}/{f}" for f in subfiles]

        return files

    # -------------------------------------------------------------------------
    # Recursive directory transfers
    # -------------------------------------------------------------------------

    @classmethod
    def copy_local_to_remote_directory(
        cls,
        local: str | Path,
        remote: str | Path,
        overwrite: bool = False,
    ) -> str:
        """
        Recursively copies a local directory to the remote server, preserving
        the subfolder structure. Remote directories are created as needed.

        The entire transfer reuses a single SSH/SFTP session, and files already
        present on the remote are skipped -- making this safe (and fast) to
        re-run for interrupted transfers.

        #### Parameters

        - `local`:
            The local directory whose contents will be copied.
        - `remote`:
            The remote directory to copy into. Created if it does not exist.
        - `overwrite`:
            Whether to re-copy files that already exist on the remote. Defaults
            to False.

        #### Returns

        - `remote`:
            The remote directory as a POSIX-style string.
        """
        local_dir = Path(local)
        if not local_dir.is_dir():
            raise Exception(f"'{local_dir}' is not an existing local directory")
        remote_dir = cls._to_remote_str(remote)

        # everything in the local tree, as POSIX paths relative to `local_dir`.
        # Folders are tracked separately so that empty ones are still recreated.
        contents = sorted(local_dir.rglob("*"))
        files = [f.relative_to(local_dir).as_posix() for f in contents if f.is_file()]
        folders = [f.relative_to(local_dir).as_posix() for f in contents if f.is_dir()]

        with cls._sftp_session() as sftp:

            # skip files that made it over on a previous (interrupted) run
            if not overwrite and cls.exists_remote(remote_dir, sftp=sftp):
                already_copied = set(cls.walk_remote(remote_dir, sftp=sftp))
                files = [f for f in files if f not in already_copied]

            # Each folder is made once, rather than once per file inside it.
            # `rglob` above gives every subfolder, so this covers all parents.
            # The base dir is included so it is made even when there are no files.
            for folder in [""] + folders:
                cls.mkdir_remote(f"{remote_dir}/{folder}", sftp=sftp)

            for file in track(files, description="Copying to remote..."):
                sftp.put(
                    remotepath=f"{remote_dir}/{file}",
                    localpath=str(local_dir / file),
                )

        return remote_dir

    @classmethod
    def copy_remote_to_local_directory(
        cls,
        local: str | Path,
        remote: str | Path,
        overwrite: bool = False,
    ) -> Path:
        """
        Recursively copies a remote directory to the local filesystem,
        preserving the subfolder structure. Local directories are created as
        needed.

        The entire transfer reuses a single SSH/SFTP session, and files already
        present locally are skipped -- making this safe (and fast) to re-run
        for interrupted transfers.

        #### Parameters

        - `local`:
            The local directory to copy into. Created if it does not exist.
        - `remote`:
            The remote directory whose contents will be copied.
        - `overwrite`:
            Whether to re-copy files that already exist locally. Defaults to
            False.

        #### Returns

        - `local`:
            The path to the local directory as a `pathlib.Path` object.
        """
        from simmate.utils.files import get_directory

        local_dir = get_directory(local)
        remote_dir = cls._to_remote_str(remote)

        with cls._sftp_session() as sftp:

            # skip files that made it over on a previous (interrupted) run
            files = [
                f
                for f in sorted(cls.walk_remote(remote_dir, sftp=sftp))
                if overwrite or not (local_dir / f).exists()
            ]

            # each folder is made once, rather than once per file inside it
            for folder in {(local_dir / f).parent for f in files}:
                folder.mkdir(parents=True, exist_ok=True)

            for file in track(files, description="Copying from remote..."):
                sftp.get(
                    remotepath=f"{remote_dir}/{file}",
                    localpath=str(local_dir / file),
                )

        return local_dir
