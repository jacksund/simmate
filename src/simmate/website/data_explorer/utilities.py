# -*- coding: utf-8 -*-

import logging


def build_and_upload_downloads():
    """
    Exports and uploads archive files for all datasets shown on the
    data explorer homepage.

    This runs `export_and_upload` on each table, producing both CSV and
    Parquet zip files and uploading them to S3.

    #### Example

        ```python
        from simmate.website.data_explorer.utilities import build_and_upload_downloads
        build_and_upload_downloads()
        ```
    """

    from simmate.database import connect  # isort: skip

    from simmate.apps.aflow.models import AflowPrototype
    from simmate.apps.chembl.models import ChemblMolecule
    from simmate.apps.cod.models import CodStructure
    from simmate.apps.jarvis.models import JarvisStructure
    from simmate.apps.materials_project.models import MatprojStructure
    from simmate.apps.oqmd.models import OqmdStructure

    tables = [
        AflowPrototype,
        CodStructure,
        JarvisStructure,
        MatprojStructure,
        OqmdStructure,
        ChemblMolecule,
    ]

    for table in tables:
        logging.info(f"--- Processing {table.table_name} ---")
        table.export_and_upload(columns="minimal")

    logging.info("All downloads built and uploaded.")
