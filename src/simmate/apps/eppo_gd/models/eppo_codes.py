# -*- coding: utf-8 -*-

import logging
import warnings

import requests
from bs4 import BeautifulSoup
from rich.progress import track

from simmate.database.base_data_types import DatabaseTable, table_column


class EppoCode(DatabaseTable):
    """
    EPPO Codes are labels to provide all pest-specific information that has been
    produced or collected by the European and Mediterranean Plant Protection
    Organization (EPPO)

    This table includes codes and metadata pulled lazily from the official
    [EPPO website](https://gd.eppo.int/).

    Note that some organizations (such as Corteva) use internal codes as well,
    so this table can include additional codes with a custom "eppo_source".
    """

    # disable cols
    source = None

    html_display_name = "EPPO"
    html_description_short = (
        "EPPO codes and metadata for >95k species of interest to agriculture."
    )

    external_website = "https://gd.eppo.int/"

    id = table_column.CharField(max_length=25, primary_key=True)
    """
    The ID is the actual EPPO code. Typically these are no more than 6 characters
    but some internal codes may be longer.
    """

    eppo_source = table_column.CharField(max_length=25, blank=True, null=True)
    """
    Where the EPPO code originated from. Typically this is "eppo_global_db",
    but can sometime be an separate source such as "corteva".
    """

    preferred_name = table_column.TextField(blank=True, null=True)
    """
    The preferred name for this entry. Typically this is the preferred
    scientific name and matches its species name. However, this field can
    be overwritten to a preferred common name if desired.
    """

    common_names = table_column.JSONField(blank=True, null=True)
    """
    A list of common names that are used for this species (e.g. "stinkbug")
    """

    other_scientific_names = table_column.JSONField(blank=True, null=True)
    """
    A list of alternative scientific names that are used for this species
    """

    # --- BEGIN TAXONOMY FIELDS ---

    kingdom = table_column.TextField(blank=True, null=True)
    """
    The "kingdom" for this entry's taxonomy tree
    """

    phylum = table_column.TextField(blank=True, null=True)
    """
    The "phylum" for this entry's taxonomy tree
    """

    subphylum = table_column.TextField(blank=True, null=True)
    """
    The "subphylum" for this entry's taxonomy tree
    """

    # BUG: I can't set this name to just class
    #   https://stackoverflow.com/questions/73838954
    class_name = table_column.TextField(blank=True, null=True, db_column="class")
    """
    The "class" for this entry's taxonomy tree
    """

    subclass = table_column.TextField(blank=True, null=True)
    """
    The "subclass" for this entry's taxonomy tree
    """

    category = table_column.TextField(blank=True, null=True)
    """
    The "category" for this entry's taxonomy tree
    """

    order = table_column.TextField(blank=True, null=True)
    """
    The "order" for this entry's taxonomy tree
    """

    suborder = table_column.TextField(blank=True, null=True)
    """
    The "suborder" for this entry's taxonomy tree
    """

    family = table_column.TextField(blank=True, null=True)
    """
    The "family" for this entry's taxonomy tree
    """

    subfamily = table_column.TextField(blank=True, null=True)
    """
    The "subfamily" for this entry's taxonomy tree
    """

    genus = table_column.TextField(blank=True, null=True)
    """
    The "genus" for this entry's taxonomy tree
    """

    species = table_column.TextField(blank=True, null=True)
    """
    The "species" for this entry's taxonomy tree
    """

    @property
    def external_link(self) -> str:
        """
        URL to this molecule in the EPPO website.
        """
        # ex: https://gd.eppo.int/taxon/LAPHEG
        return f"https://gd.eppo.int/taxon/{self.id}"

    # -------------------------------------------------------------------------

    @classmethod
    def _load_data(cls, update_only: bool = False, **kwargs):
        """
        Only use this function if you are part of the Simmate dev team!
        Users should instead access data via the load_remote_archive method.

        Loads all EPPO codes directly for the EPPO website into the local
        Simmate database.
        """

        if update_only and cls.objects.exists():
            existing_codes = list(cls.objects.values_list("id", flat=True).all())
        else:
            existing_codes = []

        all_data = EppoWebScrapper.get_all_eppo_code_data(
            skip_codes=existing_codes,
            **kwargs,
        )

        for entry in all_data:

            entry["id"] = entry.pop("eppo_code")

            # BUG-FIX: "class" key must be "class_name" to work
            if "class" in entry.keys():
                entry["class_name"] = entry.pop("class")

            # BUG-FIX: replace encoding issues
            if "other_scientific_names" in entry.keys():
                entry["other_scientific_names"] = [
                    n.replace("è", "e").replace("é", "e")
                    for n in entry.pop("other_scientific_names")
                ]
            if "common_names" in entry.keys():
                entry["common_names"] = [
                    n.replace("è", "e").replace("é", "e")
                    for n in entry.pop("common_names")
                ]
            if "subfamily" in entry.keys():
                entry["subfamily"] = entry.pop("subfamily").replace("ö", "o")

            # remove some unwanted fields
            entry.pop("name_authority", None)

            new_db_obj = cls(**entry)
            new_db_obj.save()  # consider get_or_create to update things


class EppoWebScrapper:

    @classmethod
    def get_all_eppo_code_data(cls, skip_codes: list[str] = [], **kwargs) -> list[dict]:
        return [
            cls.get_eppo_code_data(code)
            for code in track(cls._get_corteva_eppo_codes(**kwargs))
            if code not in skip_codes
        ]

    @classmethod
    def get_eppo_code_data(cls, eppo_code: str) -> dict:
        html_obj = cls._get_html_for_eppo_code(eppo_code)
        return (
            cls._parse_html_data(html_obj)
            if html_obj
            # As of 2024/03/08: 122 out of the 580 eppo codes in corteva DDV
            # do not have a match to the official eppo database. For these,
            # we mark them them as "internal"
            else {"eppo_code": eppo_code, "eppo_source": "corteva"}
        )

    @staticmethod
    def _get_corteva_eppo_codes(**kwargs) -> list[str]:

        # local import because this is a dev-only dependency
        from simmate_corteva.datasets.oracle import DDVConnection

        # establish connection & grab unique codes
        corteva_ddv = DDVConnection(**kwargs)
        return corteva_ddv.get_eppo_codes()

    @staticmethod
    def _get_html_for_eppo_code(eppo_code: str) -> BeautifulSoup:

        eppo_code_url = f"https://gd.eppo.int/taxon/{eppo_code}"

        # BUG: disable verify bc of Corteva SSL & silence warnings from not
        # using the verify fxn
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            response = requests.get(eppo_code_url, verify=False)

        if response.status_code == 200:
            html_content = response.text
        elif response.status_code == 404:
            logging.warning(f"Failed to find EPPO code: {eppo_code}")
            return None
        else:
            raise Exception(
                f"Failed to retrieve the page. Status code: {response.status_code}"
            )

        return BeautifulSoup(html_content, "html.parser")

    @staticmethod
    def _parse_html_data(html_data: BeautifulSoup) -> dict:

        # their site doesn't include html IDs or names, so we are stuck using html
        # element types (<div>, <table>, <span>, etc) and searching by text + classes

        # all sections of data are encapsulated with a div that has class='process-meta'
        header_divs = html_data.find_all(class_="process-meta")

        # the order of these divs seems to be consistent - however, not all pages have
        # all sections. we therefore iterate and figure out what we have on the fly
        data_final = {"eppo_source": "eppo_global_db"}
        for header_div in header_divs:

            # The first text of each section shows it's content. This is in a <span>
            # that is the first element in the main <div>
            header_text = header_div.text

            if header_text == "Basic information":
                # The <ul> list is 2 elements away
                data_div = header_div.find_next().find_next()

                # This next line converts the list elements to a format of:
                #   [['EPPO Code', 'LAPHEG'], ['Preferred name', 'Spodoptera exigua'], ...]
                # and then to a dictionary
                data = [
                    [x.strip() for x in i.text.split(":")]
                    for i in data_div.find_all("li")
                ]
                data = {key: value for key, value in data}

                # and take the final data and add what we want to the final dict
                data_final["eppo_code"] = data.get("EPPO Code", None)
                data_final["preferred_name"] = data.get("Preferred name", None)
                data_final["name_authority"] = data.get("Authority", None)

            elif header_text == "Other scientific names":
                # The <table> is 2 elements away
                data_div = header_div.find_next().find_next()

                # This next line converts the list elements to a format of:
                #   [['Name', 'Authority'], ['Caradrina exigua', '(Hübner)'], ...]
                data = [
                    [x.strip() for x in i.text.strip().split("\n")]
                    for i in data_div.find_all("tr")
                ]

                # the first entry is the column headers. After that, we only want
                # the first entry/column, which is the scientific name
                data_final["other_scientific_names"] = [row[0] for row in data[1:]]

            elif header_text in ["Common names", "Other names"]:
                # The <table> is 2 elements away
                data_div = header_div.find_next().find_next()

                # This next line converts the list elements to a format of:
                #   [['Name', 'Language'], ['inch worm', 'English'], ...]
                data = [
                    [x.strip() for x in i.text.strip().split("\n")]
                    for i in data_div.find_all("tr")
                ]

                # the first entry is the column headers. After that, we only want
                # the first entry/column, which is the common name
                data_final["common_names"] = [
                    name for name, auth in data[1:] if auth == "English"
                ]

            elif header_text == "Taxonomy":
                # The list of <div>'s is 2 elements away
                data_div = header_div.find_next().find_next()

                # This next line converts the list elements to a format of:
                #   [['Kingdom', 'Animalia', '1ANIMK'],
                #    ['Phylum', 'Arthropoda', '1ARTHP'],
                #    ... ]
                data = [
                    [
                        x.strip()
                        for x in i.text.strip()
                        .replace("(", "")
                        .replace(")", "")
                        .split("\r\n")
                    ]
                    for i in data_div.find_all(class_="pline")
                ]
                data = {
                    category.lower(): name.lower() for category, name, eppo_code in data
                }

                data_final.update(**data)

            elif header_text in [
                "Notes",
                "Associated Non-Taxonomic",
                "Classification",
                "Associated Taxon",
                "Photos",
            ]:
                continue  # we don't capture these sections for now

            else:
                raise Exception(f"Unknown header found in html: {header_text}")

        return data_final
