# -*- coding: utf-8 -*-

from simmate.toolkit import Structure
from simmate.toolkit.diffusion import MigrationImages
from simmate.workflow_engine import task


@task
def get_migration_images_from_endpoints(supercell_start, supercell_end):
    """
    Simple wrapper for from_endpoints method that makes it a Prefect task.
    I assume parameters for now.
    """

    # Make sure we have toolkit objects, and if not, convert them
    supercell_start_cleaned = Structure.from_dynamic(supercell_start)
    supercell_end_cleaned = Structure.from_dynamic(supercell_end)

    # Then generate the images
    images = MigrationImages.from_endpoints(
        structure_start=supercell_start_cleaned,
        structure_end=supercell_end_cleaned,
        nimages=5,  # TODO: have from_endpoints figure out pathway length
    )

    return images
