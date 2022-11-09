# -*- coding: utf-8 -*-

from simmate.toolkit import Structure
from simmate.toolkit.diffusion import MigrationImages


def get_migration_images_from_endpoints(
    supercell_start: Structure,
    supercell_end: Structure,
    nimages: int = 5,
):
    """
    Simple wrapper for from_endpoints method that makes it a Prefect task.
    I assume parameters for now.
    """

    return images
