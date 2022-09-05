# -*- coding: utf-8 -*-

import logging
from pathlib import Path

from rich.progress import track

from simmate.toolkit import Structure
from simmate.utilities import get_directory


def write_and_submit_structures(
    structures: list[Structure],
    foldername: Path,
    workflow,  # cant set type because a database module depends on this method
    workflow_kwargs: dict,
):
    if not structures:
        return

    logging.info("Writing CIFs and submitting structures")

    # sort structure by increasing size (smallest first)
    structures.sort(key=lambda s: s.num_sites)

    # disable the logs while we submit
    logger = logging.getLogger()
    logger.disabled = True

    directory = get_directory(foldername)
    for i, s in enumerate(track(structures)):

        i_cleaned = str(i).zfill(3)  # converts 1 to 001
        s.to("cif", directory / f"{i_cleaned}.cif")

        workflow.run_cloud(
            structure=s,
            **workflow_kwargs,
        )

    logger.disabled = False
