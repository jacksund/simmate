# -*- coding: utf-8 -*-

"""
Packages a desktop app into a single-file executable with PyInstaller.
"""

import logging
import os
import tempfile
from pathlib import Path


def build_executable(
    entry_script: Path,
    name: str,
    output_dir: Path,
    console: bool = False,
    extra_args: list[str] | None = None,
) -> None:
    """
    Packages the app that `entry_script` launches into a single-file executable.

    The result only runs on the OS it was built on: build on Windows for a
    `.exe`, on macOS for a Mac binary, etc.

    The theme's icons are bundled too, so apply any `theme.configure` overrides
    before calling this.

    Args:
        entry_script: The script PyInstaller runs (e.g. `simmate/desktop/__main__.py`).
            It must use absolute imports.
        name: Name of the executable.
        output_dir: Directory where the executable will be written.
        console: Whether to show a console window alongside the app.
        extra_args: More PyInstaller arguments, e.g. `--add-data=...` or
            `--copy-metadata=...` for apps that build on Simmate's desktop app.
    """
    import PyInstaller.__main__

    from simmate.desktop import theme

    # PyInstaller only collects code, so add the icons, each at the same spot
    # within its package so `Path(package.__file__)` still finds it
    icons = {theme.ICON_PATH, theme.TITLE_ICON_PATH or theme.ICON_PATH}
    icon_args = [f"--add-data={icon}{os.pathsep}{_bundle_dir(icon)}" for icon in icons]

    # build/ and .spec files are only intermediates, so keep them out of the cwd
    with tempfile.TemporaryDirectory() as work_dir:
        args = [
            str(entry_script),
            "--onefile",
            "--noconfirm",
            f"--name={name}",
            f"--distpath={output_dir}",
            f"--workpath={work_dir}",
            f"--specpath={work_dir}",
            # PyOpenGL selects its platform backend at runtime, which
            # PyInstaller can't detect on its own
            "--collect-submodules=OpenGL.platform",
            # simmate/__init__.py reads its version from package metadata
            "--copy-metadata=simmate",
            "--console" if console else "--windowed",
            *icon_args,
            *(extra_args or []),
        ]
        logging.info(f"Running PyInstaller with: {' '.join(args)}")
        PyInstaller.__main__.run(args)

    logging.info(f"Done! Your executable is in: {output_dir}")


def _bundle_dir(file: Path) -> str:
    """`file`'s folder, relative to the folder holding its top-level package."""
    packages = [folder for folder in file.parents if (folder / "__init__.py").exists()]
    return file.parent.relative_to(packages[-1].parent).as_posix()
