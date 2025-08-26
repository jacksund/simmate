# -*- coding: utf-8 -*-

import logging

from rich.progress import track

from simmate.apps.rdkit.models import Molecule
from simmate.database.base_data_types import table_column

from ..web_scraper import PPdbWebScraper


class PpdbMolecule(Molecule):
    """
    The PPDB is the 'Pesticide Properties DataBase' from a team at the
    University of Hertfordshire.

    There is both a base website and a mirror in the IUPAC website:
    - https://sitem.herts.ac.uk/aeru/ppdb/en/index.htm
    - https://sitem.herts.ac.uk/aeru/iupac/index.htm

    This table is pulled from the base website using the full index of compounds
    located here:
    - https://sitem.herts.ac.uk/aeru/ppdb/en/atoz.htm
    """

    class Meta:
        db_table = "ppdb__molecules"

    # disable cols
    source = None

    html_display_name = "PPDB"
    html_description_short = "The Pesticide Properties Database."

    html_entries_template = "ppdb/molecules/table.html"
    html_entry_template = "ppdb/molecules/view.html"

    external_website = "https://sitem.herts.ac.uk/aeru/ppdb/en/index.htm"
    source_doi = "https://sitem.herts.ac.uk/aeru/ppdb/en/atoz.htm"

    @property
    def external_link(self) -> str:
        """
        URL to this entry in the source website.
        """
        # ex: https://sitem.herts.ac.uk/aeru/ppdb/en/Reports/1234.htm
        return f"https://sitem.herts.ac.uk/aeru/ppdb/en/Reports/{self.id}.htm"

    # -------------------------------------------------------------------------

    @classmethod
    def _load_data(cls, update_only: bool = False, **kwargs):
        """
        Only use this function if you are part of the Simmate dev team!
        Users should instead access data via the load_remote_archive method.

        Loads all molecules directly for the BCPC website into the local
        Simmate database.
        """

        if update_only and cls.objects.exists():
            existing_ids = list(cls.objects.values_list("id", flat=True).all())
        else:
            existing_ids = []

        all_data = PPdbWebScraper.get_all_data(
            skip_ids=existing_ids,
            **kwargs,
        )

        logging.info("Saving to simmate database...")
        for entry_data in track(all_data):
            entry_id = entry_data.pop("id")
            cls.objects.update_or_create(
                id=entry_id,
                defaults=cls.from_toolkit(
                    as_dict=True,
                    **entry_data,
                ),
            )

        logging.info("Adding molecule fingerprints...")
        cls.populate_fingerprint_database()
