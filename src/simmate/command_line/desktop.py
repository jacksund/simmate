"""
This defines commands for the Simmate desktop app. All commands are accessible
through the `simmate desktop` command.
"""

from pathlib import Path

import typer

from simmate.command_line.utilities import AlphabeticalGroup

desktop_app = typer.Typer(rich_markup_mode="markdown", cls=AlphabeticalGroup)


@desktop_app.callback(no_args_is_help=True)
def desktop():
    """
    Commands for launching and building the Simmate desktop app.
    """


@desktop_app.command()
def start():
    """
    Launches the desktop app and blocks until its window is closed.

    Requires the `desktop` extra dependencies (e.g. `pip install simmate[desktop]`).
    """
    from simmate.desktop import main

    main()


@desktop_app.command()
def build(
    output_dir: Path = typer.Option(
        Path.cwd() / "dist",
        "--output-dir",
        help="Directory where the executable will be written.",
        resolve_path=True,
    ),
    name: str = typer.Option(
        "simmate-desktop",
        "--name",
        help="Name of the executable.",
    ),
    console: bool = typer.Option(
        False,
        "--console/--no-console",
        help="Show a console window alongside the app (useful for debugging).",
    ),
):
    """
    Packages the desktop app into a single-file executable using PyInstaller.

    The result only runs on the OS it was built on: build on Windows for a
    `.exe`, on macOS for a Mac binary, etc.

    Requires the `desktop` and `dev` extra dependencies (PyInstaller is in `dev`).

    Note: importing `simmate` also imports django and pymatgen, so these are
    bundled too and the executable will be fairly large.
    """
    import simmate.desktop
    from simmate.desktop.build import build_executable

    build_executable(
        entry_script=Path(simmate.desktop.__file__).parent / "__main__.py",
        name=name,
        output_dir=output_dir,
        console=console,
    )


@desktop_app.command()
def upload(
    output_dir: Path = typer.Option(
        Path.cwd() / "dist",
        "--output-dir",
        help="Directory holding the executable from `simmate desktop build`.",
        resolve_path=True,
    ),
    name: str = typer.Option(
        "simmate-desktop",
        "--name",
        help="Name of the executable.",
    ),
):
    """
    Uploads the executable from `simmate desktop build` to the configured S3
    bucket (`settings.s3`), at `desktop/<name>-<version>-<os>` (plus `.exe` on
    Windows), where `<version>` is the installed Simmate version.

    Re-uploading the same version replaces that version's file. Run it on the
    OS the executable was built on, since that OS goes into the file name.
    """
    import platform

    import simmate
    from simmate.database.external_connectors.s3 import SimmateS3Bucket
    from simmate.desktop.build import get_release_filename
    from simmate.utils import logger

    # PyInstaller only adds an extension on Windows
    suffix = ".exe" if platform.system() == "Windows" else ""
    executable = output_dir / f"{name}{suffix}"
    if not executable.exists():
        raise typer.BadParameter(
            f"No executable at {executable}. Run `simmate desktop build` first."
        )

    s3_key = f"desktop/{get_release_filename(simmate.__version__, name)}"
    logger.info(f"Uploading {executable} to S3...")
    SimmateS3Bucket.upload_file(executable, s3_key)
    logger.info(f"Uploaded to s3://{SimmateS3Bucket.bucket}/{s3_key}")
