# -*- coding: utf-8 -*-

import os
from pathlib import Path

from simmate.configuration import settings

from .s3_workflow import S3Workflow


class Maintenance__Postgres__PgDump(S3Workflow):
    use_database = False
    monitor = False

    command = "pg_dump"

    def get_final_command(
        command: str,
        output_file: str | Path = "pg_dump.sql",
        exclude: list[str] = [],
        data_only: bool = False,
        schema_only: bool = False,
        **kwargs,
    ) -> str:

        db = settings.database

        if db.engine != "django.db.backends.postgresql":
            raise Exception(
                "This workflow uses the default simmate database. It must be a "
                f"postgresql database but you have `{db.engine}`"
            )

        # TODO: find a better way to provide the password in a secure manner
        # The PGPASSWORD='{db.password}' at the start effectively set the ENV
        # variable right before the actual command is called
        os.environ["PGPASSWORD"] = db.password
        final_command = (
            # PGPASSWORD='{db.password}'
            f'{command} --file="{output_file}" '
            f'--host="{db.host}" --port={db.port} '
            f'--username="{db.user}" --dbname="{db.name}" '
            "--verbose --format=c --blobs "
        )

        if data_only:
            final_command += "--data-only "
        if schema_only:
            final_command += "--schema-only "

        for table_to_exclude in exclude:
            final_command += f"--exclude-table '{table_to_exclude}' "

        return final_command
