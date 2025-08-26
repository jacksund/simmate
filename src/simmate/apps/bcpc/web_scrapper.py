# -*- coding: utf-8 -*-

import logging
import warnings
from io import StringIO

import numpy
import pandas
import requests
from bs4 import BeautifulSoup
from rich.progress import track

from simmate.toolkit import Molecule

from .data import BCPC_NEWS_ARCHIVE

# from simmate.apps.chatbot import get_llm # TODO


class BcpcWebScrapper:

    @classmethod
    def get_all_data(
        cls,
        skip_names: list[str] = [],
        include_news: bool = False,
        **kwargs,
    ) -> list[dict]:
        name_data = cls.get_all_name_data()

        if include_news:
            news_data = cls.get_all_news_data()

            for entry in name_data:
                try:
                    matches = [
                        e for e in news_data if entry["name"] == e["chemical_name"]
                    ]
                    if not matches:
                        entry["company"] = None
                        entry["created_at_original"] = None
                    elif len(matches) == 1:
                        entry["company"] = matches[0]["company"]
                        entry["created_at_original"] = matches[0]["date_added"]
                    else:
                        df = pandas.DataFrame(matches)
                        df.sort_values(by="date_added", inplace=True)
                        entry["company"] = (
                            df[df.company.notna()].loc[0]["company"]
                            if not df[df.company.notna()].empty
                            else None
                        )
                        entry["created_at_original"] = df.loc[0]["date_added"]
                except:
                    continue

        # for-loop above merged news_data into the name_data
        return name_data

    # -------------------------------------------------------------------------

    # TODO: move to base class

    @staticmethod
    def get_html(url: str) -> BeautifulSoup:

        # BUG: disable verify bc of Corteva SSL & silence warnings from not
        # using the verify fxn
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            response = requests.get(url, verify=False)

        if response.status_code == 200:
            html_content = response.text
        else:
            raise Exception(
                f"Failed to retrieve the page. Status code: {response.status_code}"
            )

        return BeautifulSoup(html_content, "html.parser")

    # -------------------------------------------------------------------------

    @classmethod
    def get_all_name_data(cls, skip_names: list[str] = [], **kwargs) -> list[dict]:
        all_data = []
        for iso_name in track(cls.get_all_name_links(**kwargs)):
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
    def get_all_name_links(cls, **kwargs) -> list[str]:

        logging.info("Loading all common names from index...")
        index_url = "http://www.bcpcpesticidecompendium.org/index_cn.html"
        html_data = cls.get_html(index_url)

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

    @classmethod
    def get_name_data(cls, name: str) -> dict:
        iso_url = f"http://www.bcpcpesticidecompendium.org/{name}"
        html_data = cls.get_html(iso_url)

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
                #     'acaricides', '(something1; something example2)',
                #     'insecticides', '(avermectin)',
                #     'nematicides', '(avermectin)'
                # ]
                data = section_content.split("\n")

                discipline_types = []
                class_types = []
                for row in data:
                    entries = [
                        e.strip()
                        for e in row.replace("(", ";").replace(")", "").split(";")
                    ]
                    discipline_types += [entries[0]]
                    class_types += entries[1:]

                data_final["disciplines"] = list(set(discipline_types))
                data_final["pesticide_classes"] = list(set(class_types))

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
                molecules = [Molecule.from_inchi(i) for i in inchis]
                combined_mol = sum(molecules)

                data_final["molecule"] = combined_mol
                data_final["molecule_original"] = combined_mol.to_inchi()

            else:
                raise Exception(f"Unknown header found in html: {section_header}")

        return data_final

    # -------------------------------------------------------------------------

    # Some data is only available in the news archives... This includes:
    # - date added
    # - company
    # - description
    # Further, the company name is within the description so AI is needed to
    # pull it out. On top of that, the archive format has changed over the years.
    # For that reason, we just have AI parse all of the archives

    @classmethod
    def get_all_news_data(cls, use_cache: bool = True) -> list[dict]:

        # the 'cache' is just a CSV from running this fxn previously. Helps
        # save on LLM calls and includes a bit of manual cleanup
        if use_cache:
            return BCPC_NEWS_ARCHIVE

        all_data = []
        for xml_name in track(cls.get_all_news_links()):

            # Their website is unstable and inconsistent, so I just skip those
            # that fail. Most cases, this is a website disconnect so things
            # should work the next time this function is ran.
            try:
                entry_data = cls.get_news_data(xml_name)
                all_data += entry_data
            except:
                logging.warning(f"Failed to load {xml_name}")

        return all_data

    @classmethod
    def get_all_news_links(cls) -> list[str]:

        logging.info("Loading all news archives from index...")
        index_url = "http://www.bcpcpesticidecompendium.org/news/index.html"
        html_data = cls.get_html(index_url)

        # all links look like "pesticides-2004.xml", "pesticides-2005.xml", etc.
        links = [
            l.get("href")
            for l in html_data.find_all("a")
            if l.get("href")
            and l.get("href").startswith("pesticides-")
            and l.get("href").endswith(".xml")
        ]

        # remove duplicates and sort alphabetically
        links = list(set(links))
        links.sort()

        logging.info(f"Done. Found {len(links)} names.")
        return links

    @classmethod
    def get_news_data(cls, xml_name: str) -> dict:
        iso_url = f"http://www.bcpcpesticidecompendium.org/news/{xml_name}"
        html_data = cls.get_html(iso_url)

        llm = get_llm()
        prompt = f"""
        Below is some html/xml containing data. Create a table with columns for 
        chemical_name, company, and date_added from the data. Output
        your response as a CSV that can be loaded via pandas. Do not include 
        anything else in your response other than the CSV data (no code block 
        or anything).
        
        Some notes:
        - so be sure to use correct datetime format (e.g. 2004-06-24 13:00:00)
        - the chemical_name is typically in the title (e.g. 'sulfoxamyl')
        - the date_added is typically listed as pubDate or Date
        - the source (e.g. 'Compendium of Pesticide Common Names') is NOT
        the company name. The company name is typically within the description
        - when information does not exist for a column, leave it as null/None
        - be extra safe and just give all columns as quoted/escaped

        Here is the html/xml:
            
        {html_data}
        """
        response = llm.invoke(prompt)

        data_io = StringIO(response.content)
        df = pandas.read_csv(data_io)
        df = df.replace({numpy.nan: None})
        return df.to_dict(orient="records")
