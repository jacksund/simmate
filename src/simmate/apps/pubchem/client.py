# -*- coding: utf-8 -*-

import logging

import requests
from bs4 import BeautifulSoup

from simmate.configuration import settings
from simmate.toolkit import Molecule
from simmate.utilities import download_file, get_directory


class PubChemClient:

    # DEV-NOTE:
    # You can do a lot of this with PubChemPy, but that package hasn't been updated
    # since 2016, and it's pretty outdated. We just implement our version
    # here that uses requests instead of urlopen

    PUBCHEM_URL_BASE = "https://pubchem.ncbi.nlm.nih.gov/rest"
    PUBCHEM_DATA_ENDPOINT = "property/Title,CanonicalSMILES/JSON"

    @classmethod
    def _get_data_from_endpoint(cls, url: str) -> dict:
        cid_api_url = cls.PUBCHEM_URL_BASE + url + cls.PUBCHEM_DATA_ENDPOINT
        cid_response = requests.get(cid_api_url)
        cid_response.raise_for_status()
        cid_data = cid_response.json()

        # parse out into Simmate format
        props = cid_data["PropertyTable"]["Properties"][0]
        smiles = props["ConnectivitySMILES"]  # BUG: why a name change?
        cid_data_cleaned = {
            "pubchem_id": props["CID"],
            "common_name": props["Title"],
            "molecule": Molecule.from_smiles(smiles),
            "molecule_original": smiles,
        }

        # extra url hit for synonyms & other metadata once we have the CID
        # OPTIMIZE: see methods below for grabbing a comopunds FULL dataset
        # For now I just want cas_number
        # cid_data_cleaned["cas_number"] = cls.get_cas_from_cid(props["CID"])

        return cid_data_cleaned

    # -------------------------------------------------------------------------

    @classmethod
    def get_data_from_name(cls, name: str) -> dict:
        return cls._get_data_from_endpoint(f"/pug/compound/name/{name}/")

    @classmethod
    def get_data_from_cas_number(cls, cas_number: str) -> dict:
        # There really isn't a CAS lookup, but searching the name endpoint
        # using the CAS number gives good results
        return cls.get_data_from_name(name=cas_number)

    @classmethod
    def get_data_from_molecule(cls, molecule: Molecule) -> dict:
        query_inchi_key = molecule.to_inchi_key()
        return cls._get_data_from_endpoint(f"/pug/compound/inchikey/{query_inchi_key}/")

    # -------------------------------------------------------------------------

    @classmethod
    def get_cas_from_cid(cls, cid: int) -> str:

        from simmate.apps.cas_registry.utilities import validate_cas_number

        # grab synonyms for this CID
        syn_api_url = cls.PUBCHEM_URL_BASE + f"/pug/compound/cid/{cid}/synonyms/JSON"
        syn_response = requests.get(syn_api_url)
        syn_data = syn_response.json()

        # go through synonyms and grab valid CAS numbers
        synoyms = syn_data["InformationList"]["Information"][0]["Synonym"]
        cas_numbers = [c for c in synoyms if validate_cas_number(c)]

        # revert to searching via cas which is more robust
        for cas_number in cas_numbers:
            try:
                # !!! we just use the first cas number that works
                assert cls.get_data_from_cas_number(cas_number)
                return cas_number
            except:
                continue

    # -------------------------------------------------------------------------

    # TODO: These methods are to parset the *full* PubChem webpage when we
    # want to pull even more data.

    @classmethod
    def _get_pubchem_data(cls, cid: str):
        raise NotImplementedError()

        # Step 2: call the API endpoint using the CID, which gives us much
        # more data to work with
        cid_api_url = cls.PUBCHEM_URL_BASE + f"/pug_view/data/compound/{cid}/JSON/"
        cid_response = requests.get(cid_api_url)
        cid_data = cid_response.json()

        cid_data_cleaned = cls._parse_pubchem_response(cid_data)

        return cid_data_cleaned

    @classmethod
    def _parse_pubchem_response(cls, cid_data: dict) -> dict:
        """
        Takes the full page response and parses out + flattens data into the
        format used by the Simmate table
        """

        records = cid_data["Record"]

        cleaned_data = {
            "pubchem_id": records["RecordNumber"],
            "common_name": records["RecordTitle"],
        }

        smiles = cls._get_smiles(records)
        cleaned_data["molecule"] = Molecule.from_smiles(smiles)
        cleaned_data["molecule_original"] = smiles

        # TODO: add other properties that need more cleaning. Might use LLM
        # physcial_state = cls._get_physical_state(records)

        return cleaned_data

    @classmethod
    def _get_nested_section(cls, section: dict, heading_path: list[str]):

        if not heading_path:  # empty path ends recursion
            return section

        next_heading = heading_path[0]
        for subsection in section["Section"]:
            if next_heading == subsection["TOCHeading"]:
                return cls._get_nested_section(subsection, heading_path[1:])

    @classmethod
    def _get_smiles(cls, records):
        return cls._get_nested_section(
            records,
            [
                "Names and Identifiers",
                "Computed Descriptors",
                "Canonical SMILES",
            ],
        )["Information"][0]["Value"]["StringWithMarkup"][0]["String"]

    @classmethod
    def _get_physical_state(cls, records):
        raise NotImplementedError()
        # OPTIMIZE: it might be more efficient to pass ALL metadata and ask it
        # to determine ALL properties in a single prompt + API call. But also
        # this might lead to more errors...
        # section = cls._get_nested_section(
        #     records,
        #     [
        #         "Chemical and Physical Properties",
        #         "Experimental Properties",
        #         "Physical Description",  # or "Color / Form"?
        #     ],
        # )
        # prompt = (
        #     "Given the following information, is this compound a solid, liquid, "
        #     f"or gas? Make your answer a single word. \n\n {section}"
        # )
        # Then call the llm to get an answer

    # -------------------------------------------------------------------------

    PUBCHEM_FTP_URL = "https://ftp.ncbi.nlm.nih.gov/pubchem/Compound/CURRENT-Full/SDF/"

    @classmethod
    def get_compound_file_list(cls) -> list[str]:
        """Parses the HTML directory listing to find all .gz files."""
        response = requests.get(cls.PUBCHEM_FTP_URL)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        # Look for links ending in .sdf.gz
        links = [
            a["href"]
            for a in soup.find_all("a", href=True)
            if a["href"].endswith(".sdf.gz")
        ]
        return links

    @classmethod
    def download_all_compounds(cls):

        logging.info("Starting download of PubChem data...")

        target_dir = get_directory(settings.config_directory / "pubchem")

        # 1. Get the list of all available files
        all_files = cls.get_compound_file_list()
        logging.info(f"Found {len(all_files)} files to download.")

        # 2. Iterate and download
        for filename in all_files:

            full_url = f"{cls.PUBCHEM_FTP_URL}{filename}"
            local_path = target_dir / filename

            # Check if file already exists to avoid redundant downloads
            if local_path.exists():
                logging.info(f"Skipping {filename} (already exists)")
                continue

            logging.info(f"Downloading {filename}...")
            try:
                download_file(full_url, local_path)
            except Exception as e:
                logging.warning(f"Error downloading {filename}: {e}")

        logging.info("Done!")
