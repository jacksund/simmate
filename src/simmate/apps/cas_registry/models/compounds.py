# -*- coding: utf-8 -*-

import logging
import time
import warnings

import requests
from bs4 import BeautifulSoup

from simmate.apps.rdkit.models import Molecule
from simmate.database.base_data_types import table_column
from simmate.toolkit import Molecule as ToolkitMolecule

PUBCHEM_URL_BASE = "https://pubchem.ncbi.nlm.nih.gov/rest"


class CasRegistry(Molecule):
    """
    Molecules & Compounds from the
    [CAS Common Chemistry database](https://www.cas.org/about-us)
    database *OR* from the free alternative
    [PubChem](https://pubchem.ncbi.nlm.nih.gov/).

    This is a commercial dataset; however, other third-parties make many
    CAS numbers publicaly available. For example, chemical vendors such as
    Sigma-Aldrich and Fisher Scientific have CAS numbers heavily integrated into
    their websites. At the extreme, there are efforts like PubChem which have
    full datasets of CAS numbers available for free (based on web-scraped data).

    This table is built to use either the official CAS registery or a free
    alternative like PubChem. PubChem is used by default.

    Further, the full CAS registery is >500 million molecules and is extremely
    expensive to purchase. This table is built to load "lazily". Specifically,
    the full dataset is not loaded up front. Instead, only when a CAS number
    is requested, then it is actually pulled from an API, before being loaded
    into this table. PubChem still offers a bulk download but it doesn't have
    everything we need (e.g. smiles & common names), so we also stick to
    the API for them.

    PubChem:
        - Web UI search: https://pubchem.ncbi.nlm.nih.gov/
        - API: https://pubchem.ncbi.nlm.nih.gov/docs/pug-rest
        - Bulk Download: https://pubchem.ncbi.nlm.nih.gov/source/24603#data=Annotations
        - Extra info: https://pubchem.ncbi.nlm.nih.gov/docs/about
        - PubChemPy: https://github.com/mcs07/PubChemPy/tree/master

    CAS Common Chemistry:
        - Web UI search: https://commonchemistry.cas.org/
        - API: https://helium.cas.org/integration/v1/api-docs/
        - (no bulk downloads available without purchase)
        - Extra info: https://www.cas.org/services/commonchemistry-api
    """

    # disable cols
    source = None

    html_display_name = "CAS Registry"
    html_description_short = (
        "A *limited* catalog of commercial chemicals and their associated CAS "
        "Registry Numbers"
    )

    external_website = "https://www.cas.org/about-us"

    id = table_column.CharField(max_length=15, primary_key=True)
    """
    The CAS Registry Number used to represent the compound (ex: "1039987-26-2")
    """

    pubchem_id = table_column.IntegerField(blank=True, null=True)
    """
    The matching PubChem ID (aka CID) for this compound. Note, if the official
    CAS backend is used to load the compound, this column will be empty
    """
    # TODO: link to PubChem table

    # There's a lot of data in pubchem that I can pull in. But I only pull in what
    # need for other apps right now, but I may add more over time. Full
    # parsing of things might require a LLM to make decisions or alternatively
    # I limit sections to trusted sources. See the _get_physical_state method
    # for an example.

    common_name = table_column.TextField(blank=True, null=True)
    """
    The name of this compound that is used most often. This pulls from CAS's
    (or PubChem's) page header.
    """

    physical_state = table_column.TextField(null=True, blank=True)
    """
    The reagent physical state (liquid, solid, gas) at room temperature.
    
    Note, some reagents are solids but stored in solution -- in cases such as
    these, "liquid" is used as the descriptor.
    """

    @property
    def external_link(self) -> str:
        """
        URL to this molecule in the CAS website.
        """
        # ex: https://commonchemistry.cas.org/detail?cas_rn=1039987-26-2
        return f"https://commonchemistry.cas.org/detail?cas_rn={self.id}"

    @property
    def external_link_pubchem(self) -> str:
        """
        URL to this molecule in the PubChem website.

        PubChem's site works with both CAS numbers and their own ids (CIDs).
        """
        # ex: https://pubchem.ncbi.nlm.nih.gov/compound/50-78-2
        return f"https://pubchem.ncbi.nlm.nih.gov/compound/{self.id}/"

    @staticmethod
    def validate_cas_number(cas_number: str) -> bool:
        """
        The final number in CAS numbers have are actually a check digit, which
        can help verify if you have a legitamate CAS number.

        This method check to see if the CAS number passes the "valid" check
        and is necessary when using third-party sources such as PubChem.

        Read more about validation at:
        https://www.cas.org/support/documentation/chemical-substances/checkdig
        """
        # "A CAS Registry Number includes up to 10 digits which are separated
        # into 3 groups by hyphens. The first part of the number, starting from
        # the left, has 2 to 7 digits; the second part has 2 digits. The final
        # part consists of a single check digit.
        chunks = cas_number.split("-")

        # check 1: must have 3 sections
        if len(chunks) != 3:
            return False  # FAILS

        # check 2: each section must be numerical and an integer
        try:
            primary, secondary, check_digit = [int(c) for c in chunks]
        except:
            return False  # FAILS

        # check 3: secondary digit must be 2 digits (i.e. under 100)
        if secondary >= 100:
            return False
        # if the secondary value is 1-9, then we need a leading zero. which is why
        # we format the string below

        # check 4: final section must be 1 number
        if check_digit >= 10:
            return False  # FAILS

        # check 4: make sure check_digit is expected value. See the formula at...
        #   https://www.cas.org/support/documentation/chemical-substances/checkdig
        rn_flat = str(primary) + f"{secondary:02d}"
        expected_check_digit = (
            sum([(len(rn_flat) - n) * int(i) for n, i in enumerate(rn_flat)]) % 10
        )
        if check_digit != expected_check_digit:
            return False

        # if all checks above passed
        return True

    # -------------------------------------------------------------------------

    # CAS numbers that don't actually exist but are useful to keep in the
    # dataset for various applications, such as HTE.

    special_cas_nums = {
        # in HTE we use this for "no solvent", "no base", or other placeholders
        "0000-00-0": "( no compound / control )",
    }

    @classmethod
    def _load_special_cas(cls):
        for cas, name in cls.special_cas_nums.items():
            cls.objects.update_or_create(
                id=cas,
                defaults=dict(
                    common_name=name,
                ),
            )

    # -------------------------------------------------------------------------
    # Lazy loading data methods below
    # -------------------------------------------------------------------------

    # Searching by CAS number to get molecule + metadata
    # Note: this is the most robust loading method!

    @classmethod
    def search_cas(
        cls,
        cas_number: str,
        backend: str = "PubChem",
        force_update: bool = False,
    ):

        if not force_update:
            # check the database to see if this has been searched for
            if cls.objects.filter(id=cas_number).exists():
                return cls.objects.get(id=cas_number)

        # Otherwise we need to

        is_valid = cls.validate_cas_number(cas_number)
        if not is_valid:
            raise Exception(f"{cas_number} is not a valid CAS number")

        if backend == "PubChem":
            data = cls._search_cas_pubchem(cas_number)
        elif backend == "CAS":
            data = cls._search_cas_official(cas_number)
        else:
            raise Exception(f"'{backend}' is not supported. Must be PubChem or CAS.")

        # we use update_or_create to avoid race conditions when creating
        cas_entry, is_new = cls.objects.update_or_create(
            id=cas_number,
            defaults=cls.from_toolkit(
                **data,
                as_dict=True,
            ),
        )

        # ensure the fingerprint is added
        cls.populate_fingerprint_database()
        # OPTIMIZE: should this be done elsewhere?

        return cas_entry

    @classmethod
    def _search_cas_official(cls, cas_number: str):
        raise NotImplementedError(
            "We do not yet have access to the CAS API so this feature is unavailable"
        )

    @classmethod
    def _search_cas_pubchem(cls, cas_number: str) -> dict:
        """
        Uses the PubChem REST API to get molecule information using a CAS number.

        You can do this with PubChemPy, but that package hasn't been updated
        since 2016, and it's pretty outdated. We just implement our version
        here that uses requests instead of urlopen
        """

        # Another helpful endpoint but it doesn't give us Title:
        # f"/pug/compound/name/{cas_number}/JSON"

        # Endpoint that gives us exactly the data we need and nothing more
        cid_api_url = (
            PUBCHEM_URL_BASE
            + f"/pug/compound/name/{cas_number}/property/Title,CanonicalSMILES/JSON"
        )
        cid_response = requests.get(cid_api_url)
        cid_data = cid_response.json()

        # parse out into Simmate format
        props = cid_data["PropertyTable"]["Properties"][0]
        smiles = props["CanonicalSMILES"]
        cid_data_cleaned = {
            # "cas": cas_number,  # added elsewhere
            "pubchem_id": props["CID"],
            "common_name": props["Title"],
            "molecule": ToolkitMolecule.from_smiles(smiles),
            "molecule_original": smiles,
        }
        return cid_data_cleaned

    # -------------------------------------------------------------------------

    # Searching by molecule/inchi_key to get CAS + metadata
    # Note: this is less robust. Use CAS search if you can.

    @classmethod
    def search_molecule(
        cls,
        molecule: Molecule,
        backend: str = "PubChem",
        force_update: bool = False,
    ):
        inchi_key = molecule.to_inchi_key()

        if not force_update:
            # check the database to see if this has been searched for
            if cls.objects.filter(inchi_key=inchi_key).exists():
                # BUG: do we want to allow more than one molecule match?
                return cls.objects.get(inchi_key=inchi_key)

        # Otherwise we need to search external sources
        if backend == "PubChem":
            return cls._search_molecule_pubchem(molecule, force_update)
        elif backend == "CAS":
            return cls._search_molecule_official(molecule)
        else:
            raise Exception(f"'{backend}' is not supported. Must be PubChem or CAS.")

    @classmethod
    def _search_molecule_official(cls, molecule: Molecule):
        raise NotImplementedError(
            "We do not yet have access to the CAS API so this feature is unavailable"
        )

    @classmethod
    def _search_molecule_webscrape(cls, molecule: Molecule, sleep: int = 3):
        raise NotImplementedError(
            "Web scraping their site is not allowed, so we haven't added it yet."
        )

    @classmethod
    def _search_molecule_pubchem(
        cls,
        molecule: Molecule,
        force_update: bool = False,
    ) -> str:

        # We can't do a direct lookup of CAS from a molecule, so we need
        # to instead look up the CID --> look up synonyms --> get CAS
        query_inchi_key = molecule.to_inchi_key()
        mol_api_url = (
            PUBCHEM_URL_BASE
            + f"/pug/compound/inchikey/{query_inchi_key}/property/Title,CanonicalSMILES/JSON"
        )
        mol_response = requests.get(mol_api_url)
        mol_data = mol_response.json()

        # pull out the CIDs
        # BUG: we just use the 1st result and ignore others
        query_cid = mol_data["PropertyTable"]["Properties"][0]["CID"]

        # grab synonyms for this CID
        syn_api_url = PUBCHEM_URL_BASE + f"/pug/compound/cid/{query_cid}/synonyms/JSON"
        syn_response = requests.get(syn_api_url)
        syn_data = syn_response.json()

        # go through synonyms and grab valid CAS numbers
        synoyms = syn_data["InformationList"]["Information"][0]["Synonym"]
        cas_numbers = [c for c in synoyms if cls.validate_cas_number(c)]

        # revert to searching via cas which is more robust
        # !!! we just use the first cas number that works
        for cas_number in cas_numbers:
            try:
                return cls.search_cas(
                    cas_number=cas_number,
                    backend="PubChem",
                    force_update=force_update,
                )
            except:
                continue

    # -------------------------------------------------------------------------

    # TODO: These methods are to parset the *full* PubChem webpage. This should
    # move to the PubChem table.

    @classmethod
    def _get_pubchem_data(cls, cid: str):
        raise NotImplementedError()

        api_url_base = "https://pubchem.ncbi.nlm.nih.gov/rest"

        # Step 2: call the API endpoint using the CID, which gives us much
        # more data to work with
        cid_api_url = api_url_base + f"/pug_view/data/compound/{cid}/JSON/"
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
        cleaned_data["molecule"] = ToolkitMolecule.from_smiles(smiles)
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
        # to determine ALL properties in a single prompt + API call

        section = cls._get_nested_section(
            records,
            [
                "Chemical and Physical Properties",
                "Experimental Properties",
                "Physical Description",  # or "Color / Form"?
            ],
        )

        prompt = (
            "Given the following information, is this compound a solid, liquid, "
            f"or gas? Make your answer a single word. \n\n {section}"
        )
        # Then call the llm to get an answer
