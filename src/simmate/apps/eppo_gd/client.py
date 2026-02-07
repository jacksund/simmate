# -*- coding: utf-8 -*-

import logging
import warnings

import requests
from bs4 import BeautifulSoup
from rich.progress import track


class EppoWebScrapper:

    @classmethod
    def get_all_eppo_code_data(cls, eppo_codes: list[str], **kwargs) -> list[dict]:
        return [cls.get_eppo_code_data(code, **kwargs) for code in track(eppo_codes)]

    @classmethod
    def get_eppo_code_data(
        cls, eppo_code: str, no_match_source: str = "internal"
    ) -> dict:
        html_obj = cls._get_html_for_eppo_code(eppo_code)
        return (
            cls._parse_html_data(html_obj)
            if html_obj
            # If there is no match to the official eppo database, we mark the
            # source as internal
            else {"eppo_code": eppo_code, "eppo_source": no_match_source}
        )

    @staticmethod
    def _get_html_for_eppo_code(eppo_code: str) -> BeautifulSoup:

        eppo_code_url = f"https://gd.eppo.int/taxon/{eppo_code}"

        # BUG: disable verify bc of SSL & silence warnings from not
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
