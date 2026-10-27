import logging
from pathlib import Path

from rich.progress import track

from simmate.toolkit import Structure
from simmate.utils import get_directory, logger


def write_and_submit_structures(
    structures: list[Structure],
    foldername: Path,
    workflow,  # cant set type because a database module depends on this method
    workflow_kwargs: dict,
):
    if not structures:
        return []

    logger.info("Writing CIFs and submitting structures")

    # sort structure by increasing size (smallest first)
    structures.sort(key=lambda s: s.num_sites)

    # disable the logs while we submit
    logging.disable(logging.CRITICAL)

    nalready_submitted = 0
    directory = get_directory(foldername)
    states = []
    for i, s in enumerate(track(structures)):
        # check if the structure has been submitted before, and if so, skip it
        if workflow.all_results.filter(source=s.source).exists():
            nalready_submitted += 1
            continue

        i_cleaned = str(i).zfill(3)  # converts 1 to 001
        s.to(filename=str(directory / f"{i_cleaned}.cif"), fmt="cif")

        state = workflow.run_cloud(
            structure=s,
            **workflow_kwargs,
        )
        states.append(state)

    logging.disable(logging.NOTSET)

    if nalready_submitted > 0:
        logger.info(
            f"{nalready_submitted} structures were already submitted "
            "and therefore skipped."
        )

    return states
