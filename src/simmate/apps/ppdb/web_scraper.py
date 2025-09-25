# -*- coding: utf-8 -*-

import logging
from datetime import datetime

from django.utils.timezone import make_aware
from rich.progress import track

from simmate.database.external_connectors.web_scrape import WebScraper
from simmate.toolkit import Molecule


class PpdbWebScraper(WebScraper):

    @classmethod
    def get_all_data(cls, skip_ids: list[str] = [], **kwargs) -> list[dict]:
        all_data = []
        for entry_id in track(cls.get_all_id_links(**kwargs)):
            if entry_id in skip_ids:
                continue

            # Their website is unstable and inconsistent, so I just skip those
            # that fail. Most cases, this is a website disconnect so the
            # iso_name should work the next time this function is ran.
            try:
                entry_data = cls.get_id_data(entry_id)
                all_data.append(entry_data)
            except:
                logging.warning(f"Failed to load {entry_id}")

        return all_data

    @classmethod
    def get_all_id_links(cls, **kwargs) -> list[str]:

        logging.info("Loading all entries from index...")
        index_url = "https://sitem.herts.ac.uk/aeru/ppdb/en/atoz.htm"
        html_data = cls.get_html(index_url)

        urls_to_skip = ["mailto:aeru@herts.ac.uk"]
        links = [
            a["href"].split("/")[-1].split(".")[0]
            for p in html_data.find_all("p")
            for a in p.find_all("a", href=True)
            if p.find_previous_sibling("p", class_="atoz_section_title")
            and a["href"] not in urls_to_skip
        ]

        # remove duplicates and sort alphabetically
        links = list(set(links))
        links.sort()

        logging.info(f"Done. Found {len(links)} names.")
        return links

    @classmethod
    def get_id_data(cls, entry_id: int) -> dict:
        iso_url = f"https://sitem.herts.ac.uk/aeru/ppdb/en/Reports/{str(entry_id)}.htm"
        html_data = cls.get_html(iso_url)

        data_final = {"id": entry_id}

        # Title
        element = html_data.find("td", class_="title")
        if element:
            data_final["name"] = element.text.split("(Ref:")[0].strip()

        # Subtitle / aliases
        element = html_data.find("td", class_="subtitle")
        if element:
            data_final["aliases"] = [
                s.strip() for s in element.text.strip("() ")[14:].split(";")
            ]

        # Last update
        element = html_data.find("td", class_="date")
        if element:
            date_str = element.text.strip().replace("Last updated:", "").strip()
            data_final["updated_at_original"] = make_aware(
                datetime.strptime(date_str, "%d/%m/%Y")
            )

        # Summary
        element = html_data.find("table", class_="report_summary")
        if element:
            data_final["summary"] = element.text.strip()

        # Health Issues Summary
        element = html_data.find("table", class_="report_health_issues")
        if element:
            element_data = element.text.replace("\n\n\n", "\n").split("\n")[1:-1]
            data_final["evironment_fate"] = element_data[3].split(":")[0].strip()[18:]
            data_final["ecotoxicity"] = element_data[4].split(":")[0].strip()[11:]
            data_final["human_health"] = element_data[5].split(":")[0].strip()[12:]

        # GENERAL INFORMATION SECTION
        rows = html_data.find_all("td")
        for i, row in enumerate(rows):
            if row.text == "Description":
                data_final["description"] = rows[i + 1].text
            elif row.text == "Example pests controlled":
                data_final["pests_controlled"] = [
                    t.strip() for t in rows[i + 1].text.split(";")
                ]
            elif row.text == "Example applications":
                data_final["applications"] = [
                    t.strip() for t in rows[i + 1].text.split(";")
                ]
            elif row.text == "Efficacy & activity":
                data_final["efficacy_and_activity"] = rows[i + 1].text
            elif row.text == "Availability status":
                data_final["availability_status"] = rows[i + 1].text
            elif row.text == "Introduction & key dates":
                data_final["key_dates"] = rows[i + 1].text
            elif row.text == "GB COPR regulatory status":
                # +2 in order to skip the tooltip!
                data_final["hb_copr_regulatory_status"] = rows[i + 2].text
            elif row.text == "EC Regulation 1107/2009 status":
                data_final["ec_regulatory_status"] = rows[i + 2].text
            elif row.text == "Canonical SMILES":
                data_final["molecule_original"] = rows[i + 1].text
                data_final["molecule"] = Molecule.from_smiles(rows[i + 1].text)
            elif row.text == "Pesticide type":
                data_final["pesticide_type"] = [
                    s.strip() for s in rows[i + 1].text.split(";")
                ]
            elif row.text == "Substance groups":
                data_final["substance_groups"] = [
                    t.strip() for t in rows[i + 1].text.split(";")
                ]
            elif row.text == "Mode of action":
                data_final["mode_of_action"] = rows[i + 1].text
            elif row.text == "CAS RN":
                data_final["cas_number"] = rows[i + 1].text
            elif row.text == "EC number":
                data_final["ec_number"] = rows[i + 1].text
            elif row.text == "CIPAC number":
                data_final["cipac_number"] = rows[i + 1].text
            elif row.text == "US EPA chemical code":
                data_final["us_epa_chemical_code"] = rows[i + 1].text
            elif row.text == "PubChem CID":
                data_final["pubchem_cid"] = rows[i + 1].text
            elif row.text == "CLP index number":
                data_final["clp_index_number"] = rows[i + 1].text
            elif row.text == "Examples of recorded resistance":
                data_final["known_resistances"] = rows[i + 1].text
            elif row.text == "Physical state":
                data_final["physical_state"] = rows[i + 1].text
            elif (
                row.text
                == "Example manufacturers & suppliers of products using this active now or historically"
            ):
                data_final["manufacturers_and_suppliers"] = [
                    l.text.strip() for l in rows[i + 1].select("li")
                ]
            elif row.text == "Example products using this active":
                data_final["product_names"] = [
                    l.text.strip() for l in rows[i + 1].select("li")
                ]
            elif row.text == "Formulation and application details":
                data_final["formulation_details"] = rows[i + 1].text
            elif row.text == "Commercial production":
                data_final["commercial_production_details"] = rows[i + 1].text

        # cleanup empty values
        data_final = {
            k: v
            for k, v in data_final.items()
            if v not in [None, "", "-", "No data found", "Not listed", "None allocated"]
        }

        # clean up buggy characters
        for k, v in data_final.items():
            if isinstance(v, str):
                data_final[k] = cls.replace_accents(v)
            elif isinstance(v, list) and all([isinstance(s, str) for s in v]):
                data_final[k] = [cls.replace_accents(s) for s in v]

        return data_final
