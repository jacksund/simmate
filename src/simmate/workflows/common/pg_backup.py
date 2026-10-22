import logging
from datetime import UTC, datetime, timedelta
from pathlib import Path

from ..core import Workflow
from .pg_dump import Maintenance__Postgres__PgDump


class Maintenance__Postgres__BackupToS3(Workflow):
    """
    Creates a full backup of the default simmate database (via `pg_dump`) and
    uploads it to the private S3 bucket. Backups older than `days_to_keep`
    are then removed from the bucket.

    See `SimmatePrivateS3Bucket` for how the bucket is named. It must already
    exist.

    NOTE: requires `pg_dump`, which only the `simmate-worker` image includes.

    #### Parameters

    - `days_to_keep`:
        Backups in the bucket that are older than this number of days are
        deleted. Set to None to keep all backups. Default is 3.
    - `s3_prefix`:
        The folder within the bucket to store backups in.
    """

    use_database = False  # we don't have a database table yet

    @staticmethod
    def run_config(
        command: str = None,
        directory: Path = None,
        days_to_keep: int = 3,
        s3_prefix: str = "database_backups",
        **kwargs,
    ):
        from simmate.database.external_connectors.s3 import SimmatePrivateS3Bucket

        if not SimmatePrivateS3Bucket.bucket:
            raise Exception(
                "This workflow uploads to your private S3 bucket, but no "
                "bucket is configured. Make sure `settings.s3.bucket` is set."
            )

        # create the full backup, named by date since we do daily backups
        now = datetime.now(UTC)
        filename = now.strftime("%Y_%m_%d.sql")
        dump_dir = directory / "pg_dump"
        Maintenance__Postgres__PgDump.run(
            command=command,
            directory=dump_dir,
            output_file=filename,
        )

        # upload the backup to the private bucket
        dump_file = dump_dir / filename
        s3_key = f"{s3_prefix}/{filename}"
        SimmatePrivateS3Bucket.upload_file(local_path=dump_file, s3_key=s3_key)

        # delete the local file to clear up disk space
        dump_file.unlink()

        # remove any old backups from the bucket. This is done *after* the
        # upload so that a failed backup never removes older ones.
        if days_to_keep is not None:
            cutoff = now - timedelta(days=days_to_keep)
            old_keys = [
                obj.key
                for obj in SimmatePrivateS3Bucket.list_objects(prefix=f"{s3_prefix}/")
                if obj.last_modified < cutoff and obj.key != s3_key
            ]
            SimmatePrivateS3Bucket.delete_keys(old_keys)
            logging.info(
                f"Removed {len(old_keys)} backups older than {days_to_keep} days"
            )
