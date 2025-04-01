# -*- coding: utf-8 -*-

import logging
import warnings

import requests
from bs4 import BeautifulSoup
from rich.progress import track

from simmate.apps.rdkit.models import Molecule
from simmate.database.base_data_types import table_column
from simmate.toolkit import Molecule as ToolkitMolecule


class IsoPesticides(Molecule):
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

    # disable cols
    source = None

    html_display_name = "ISO Pesticides"
    html_description_short = "A compendium of pesticides with common names."

    external_website = "http://www.bcpcpesticidecompendium.org/index.html"
    source_doi = "http://www.bcpcpesticidecompendium.org/index_cn_frame.html"

    name = table_column.TextField(blank=True, null=True)

    approval_source = table_column.TextField(blank=True, null=True)

    cas_number = table_column.TextField(blank=True, null=True)
    # TODO: link to CasRegistry table

    disciplines = table_column.JSONField(blank=True, null=True)

    pesticide_classes = table_column.JSONField(blank=True, null=True)

    notes = table_column.TextField(blank=True, null=True)

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
    def _load_data(cls, update_only: bool = False, **kwargs):
        """
        Only use this function if you are part of the Simmate dev team!
        Users should instead access data via the load_remote_archive method.

        Loads all molecules directly for the BCPC website into the local
        Simmate database.
        """

        if update_only and cls.objects.exists():
            existing_names = list(cls.objects.values_list("name", flat=True).all())
        else:
            existing_names = []

        all_data = GcpcWebScrapper.get_all_data(
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


class GcpcWebScrapper:

    @classmethod
    def get_all_data(cls, skip_names: list[str] = [], **kwargs) -> list[dict]:
        all_data = []
        for iso_name in track(cls._get_all_name_links(**kwargs)):
            if iso_name in skip_names:
                continue

            # Their website is unstable and inconsistent, so I just skip those
            # that fail. Most cases, this is a website disconnect so the
            # iso_name should work the next time this function is ran.
            try:
                entry_data = cls.get_name_data(iso_name)

                # we only want to include entries that have a compound associated with it
                if "molecule" in entry_data.keys():
                    all_data.append(entry_data)

            except:
                logging.warning(f"Failed to load {iso_name}")

        return all_data

    @classmethod
    def get_name_data(cls, name: str) -> dict:
        html_obj = cls._get_html_for_name(name)
        return cls._parse_html_data(html_obj)

    @staticmethod
    def _get_all_name_links(**kwargs) -> list[str]:

        logging.info("Loading all common names from index...")
        index_url = "http://www.bcpcpesticidecompendium.org/index_cn.html"

        # BUG: disable verify bc of Corteva SSL & silence warnings from not
        # using the verify fxn
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            response = requests.get(index_url, verify=False)

        html_data = BeautifulSoup(response.text, "html.parser")

        # Their html isn't super organized, so I grab the URLs just by inspecting
        # all links in the frame. There are some we can ingore and some that have
        # no href.
        urls_to_skip = [
            # BUG: consider fixing some of these
            "barium%20hexafluorosilicate.html",  # rdkit fails w. formal charges
            "sodium%20silicofluoride.html",  # rdkit fails w. formal charges
            "chitosan.html",  # no molecule
            "cufraneb.html",  # no molecule
            "DA-6.html",  # missing inchi
            "dimethacarb.html",  # missing inchi
            "galquin.html",  # missing inchi
            "ledprona.html",  # RNA squence
            "maltodextrin.html",  # no molecule
            "mancopper.html",  # missing inchi
            "mancozeb.html",  # missing inchi
            "metiram.html",  # missing inchi
            "pronitridine.html",  # missing inchi
            "tolylmercury%20acetate.html",  # missing inchi
            "vadescana.html",  # RNA squence
            "zinc%20naphthenate.html",  # no molecule
            "zineb.html",  # missing inchi
        ]
        links = [
            l.get("href")
            for l in html_data.find_all("a")
            if l.get("href") not in [None, "index_cn_frame.html"] + urls_to_skip
        ]

        # remove duplicates and sort alphabetically
        links = list(set(links))
        links.sort()

        logging.info(f"Done. Found {len(links)} names.")
        return links

    @staticmethod
    def _get_html_for_name(iso_url_ending: str) -> BeautifulSoup:

        iso_url = f"http://www.bcpcpesticidecompendium.org/{iso_url_ending}"

        # BUG: disable verify bc of Corteva SSL & silence warnings from not
        # using the verify fxn
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            response = requests.get(iso_url, verify=False)

        if response.status_code == 200:
            html_content = response.text
        else:
            raise Exception(
                f"Failed to retrieve the page. Status code: {response.status_code}"
            )

        return BeautifulSoup(html_content, "html.parser")

    @staticmethod
    def _parse_html_data(html_data: BeautifulSoup) -> dict:

        # BUG: some characters and formatting fail to render. Consider using...
        # https://stackoverflow.com/questions/12985456

        # their site doesn't include html IDs or names, so we are stuck using html
        # element types (<div>, <table>, <span>, etc) and searching by text + classes
        data_final = {}

        # grab the name
        data_final["name"] = html_data.find_all("h1")[0].text

        # all sections of data are encapsulated as table rows
        sections = html_data.find_all("tr")

        # the order of these divs seems to be consistent - however, not all pages have
        # all sections. we therefore iterate and figure out what we have on the fly
        for section in sections:
            section_header = section.find_all("th")[0].text

            # We want new lines to render, and bs4 skips <br> tags by default.
            # So we replace these with newline characters for our string
            section_content = section.find_all("td")[0]
            for breaktag in section_content.find_all("br"):
                breaktag.replace_with("\n")
            section_content = section_content.text

            # we don't capture these sections for now
            if section_header in [
                "Structure:",  # just images that we dont want
                "Pronunciation:",
                "IUPAC name:",  # misformated
                "IUPAC PIN:",
                "InChIKey:",
                "Formula:",
                "CAS name:",  # leaving to CAS table
            ]:
                continue

            # these vary a bunch but each page only ever has 1
            elif section_header in [
                "Approval:",
                "Approval",
                "Approved:",
                "Status:",
                "Approvals:",
            ]:
                data_final["approval_source"] = section_content

            elif section_header in ["CAS Reg. No.:", "Reg. No.:"]:
                data_final["cas_number"] = section_content

            elif section_header == "Activity:":
                # Gives a list like...
                # [
                #     'acaricides', '(avermectin)',
                #     'insecticides', '(avermectin)',
                #     'nematicides', '(avermectin)'
                # ]
                data = [
                    x for entry in section_content.split("\n") for x in entry.split()
                ]

                class_types = []
                discipline_types = []
                for value in data:
                    if value.startswith("(") and value.endswith(")"):
                        value_strip = value[1:-1]
                        if value_strip not in class_types:
                            class_types.append(value_strip)
                    else:
                        if value not in discipline_types:
                            discipline_types.append(value)
                data_final["pesticide_classes"] = class_types
                data_final["disciplines"] = discipline_types

            elif section_header == "Notes:":
                data_final["notes"] = section_content if section_content else None

            elif section_header == "InChI:":
                # The inchi keys are put in span classes, which help us ingnore
                # the sub-names attached to each, which often have wacky formatting

                inchis = []
                for inchi_section in section.find_all("span"):

                    # Ideally this is what we want , but there are a lot of
                    # broken cases that we try to cover below
                    inchi = inchi_section.text

                    # some have the inchi misplaced and outside of the span
                    if not inchi:
                        inchi = section_content

                    # Some inchis have a typo and have an extra I in "InChI".
                    if "IInChI=" in inchi:
                        inchi = inchi.replace("IInChI=", "InChI=")

                    # wrote inchi twice...
                    if "InChI=InChI=" in inchi:
                        inchi = inchi.replace("InChI=InChI=", "InChI=")

                    # Some have inchi keys pasted at the end
                    broken_keys = [
                        "USMZPYXTVKAYST-UHFFFAOYSA-N",
                        "RRNIZKPFKNDSRS-UHFFFAOYSA-N",
                        "YXWCBRDRVXHABN-UHFFFAOYSA-N",
                    ]
                    for key in broken_keys:
                        inchi = inchi.replace(key, "")

                    # Some inchi strings have extra text at the end of them
                    if " " in inchi:
                        inchi = inchi.split()[0]

                    # we should now have a cleaned inchi
                    inchis.append(inchi)

                # medlure.html manual fix
                if inchis == ["4-chloro"]:
                    inchis = [
                        "InChI=1S/C12H21ClO2/c1-4-9(3)15-12(14)11-6-5-10(13)7-8(11)2/h8-11H,4-7H2,1-3H3",
                        "InChI=1S/C12H21ClO2/c1-4-9(3)15-12(14)11-7-10(13)6-5-8(11)2/h8-11H,4-7H2,1-3H3",
                    ]

                # sometimes there are multiple molecules with separate inchi keys
                # so we combine them here.
                molecules = [ToolkitMolecule.from_inchi(i) for i in inchis]
                combined_mol = sum(molecules)

                data_final["molecule"] = combined_mol
                data_final["molecule_original"] = combined_mol.to_inchi()

            else:
                raise Exception(f"Unknown header found in html: {section_header}")

        return data_final
