# -*- coding: utf-8 -*-

import logging

from rich.progress import track

from simmate.apps.rdkit.models import Molecule
from simmate.database.base_data_types import table_column

from ..web_scraper import BcpcWebScraper


class BcpcIsoPesticide(Molecule):
    """
    This is the "Compendium of Pesticide Common Names" pulled from the
    British Crop Production Council (BCPC) website.

    This electronic compendium is intended to provide details of the status of
    all pesticide common names (not just those assigned by ISO), together with
    their systematic chemical names, molecular formulae, chemical structures
    and CAS Registry Numbers.

    These links below are the main index pages, but when you inspect, their site
    is entirely made of frames that point to other views:

        - http://www.bcpcpesticidecompendium.org/index-inchikey-frame.html
        - http://www.bcpcpesticidecompendium.org/index_cn_frame.html
    """

    class Meta:
        db_table = "bcpc__iso_pesticides__molecules"

    # disable cols
    source = None

    html_display_name = "ISO Pesticides"
    html_description_short = "A compendium of pesticides with common names."

    html_entries_template = "bcpc/iso_pesticides/table.html"
    html_entry_template = "bcpc/iso_pesticides/view.html"
    is_redistribution_allowed = False

    external_website = "http://www.bcpcpesticidecompendium.org/index.html"
    source_doi = "http://www.bcpcpesticidecompendium.org/index_cn_frame.html"

    name = table_column.TextField(blank=True, null=True)

    approval_source = table_column.TextField(blank=True, null=True)

    cas_number = table_column.TextField(blank=True, null=True)
    # TODO: link to CasRegistry table

    disciplines = table_column.JSONField(blank=True, null=True)

    pesticide_classes = table_column.JSONField(blank=True, null=True)

    notes = table_column.TextField(blank=True, null=True)

    # EXTRAS FROM "news archive" SECTION -- ugly data and many rows missing
    # company = table_column.TextField(blank=True, null=True)
    # created_at_original = table_column.DateTimeField(blank=True, null=True)

    @property
    def external_link(self) -> str:
        """
        URL to this pesticide in the BCPC website.
        """
        # ex: http://www.bcpcpesticidecompendium.org/emamectin.html
        name_encoded = self.name.replace(" ", "%20")  # to handle a space in the name
        return f"http://www.bcpcpesticidecompendium.org/{name_encoded}.html"

    # -------------------------------------------------------------------------

    @classmethod
    def load_source_data(cls, update_only: bool = False, **kwargs):
        """
        Loads all molecules directly for the BCPC website into the local
        Simmate database.
        """

        if update_only and cls.objects.exists():
            existing_names = list(cls.objects.values_list("name", flat=True).all())
        else:
            existing_names = []

        all_data = BcpcWebScraper.get_all_data(
            skip_names=existing_names,
            **kwargs,
        )

        logging.info("Saving to simmate database...")
        for entry_data in track(all_data):
            entry_name = entry_data.pop("name")
            cls.objects.update_or_create(
                name=entry_name,
                defaults=cls.from_toolkit(
                    as_dict=True,
                    **entry_data,
                ),
            )

        logging.info("Adding molecule fingerprints...")
        cls.populate_fingerprint_database()
