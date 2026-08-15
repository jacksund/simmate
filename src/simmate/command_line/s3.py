# -*- coding: utf-8 -*-

"""
This defines commands for S3 bucket operations. All commands are
accessible through the `simmate dev s3` command.
"""

from pathlib import Path

import typer

s3_app = typer.Typer(rich_markup_mode="markdown")


@s3_app.callback(no_args_is_help=True)
def s3():
    """
    Commands for uploading, downloading, and browsing the configured S3 bucket.
    """
    pass


@s3_app.command()
def upload(
    local_dir: Path = typer.Argument(
        ...,
        help="Local directory to upload.",
        exists=True,
        file_okay=False,
        resolve_path=True,
    ),
    prefix: str = typer.Argument(
        "",
        help="S3 key prefix to upload under (e.g. 'experiments/run1').",
    ),
):
    """
    Recursively uploads a local directory to the configured S3 bucket.

    Files already present in S3 are skipped.
    """
    from simmate.database.external_connectors.s3 import SimmateS3Bucket

    SimmateS3Bucket.upload_directory(local_dir, s3_prefix=prefix)


@s3_app.command()
def download(
    local_dir: Path = typer.Argument(
        ...,
        help="Local directory to sync files into.",
        resolve_path=True,
    ),
    prefix: str = typer.Argument(
        "",
        help="S3 key prefix to download from (e.g. 'experiments/run1').",
    ),
):
    """
    Recursively downloads files from the configured S3 bucket to a local directory.

    Files already present locally are skipped.
    """
    from simmate.database.external_connectors.s3 import SimmateS3Bucket

    SimmateS3Bucket.sync_directory(local_dir, s3_prefix=prefix)


@s3_app.command()
def ls(
    prefix: str = typer.Argument(
        "",
        help="S3 key prefix to list (e.g. 'experiments/').",
    ),
):
    """
    Lists the immediate contents (folders and files) at a given S3 prefix.
    """
    from simmate.database.external_connectors.s3 import SimmateS3Bucket

    contents = SimmateS3Bucket.list_contents(prefix=prefix)

    for folder in contents["folders"]:
        typer.echo(f"  📁 {folder}")
    for file in contents["files"]:
        typer.echo(f"  📄 {file}")

    if not contents["folders"] and not contents["files"]:
        typer.echo("(empty)")
