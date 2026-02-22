# -*- coding: utf-8 -*-

from simmate.apps.rdkit.models import Molecule
from simmate.database.base_data_types import table_column


class CasRegistryMolecule(Molecule):
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

    class Meta:
        db_table = "cas_registry__molecules"

    html_display_name = "CAS Registry"
    html_description_short = (
        "A *limited* catalog of commercial chemicals and their associated CAS "
        "Registry Numbers"
    )

    external_website = "https://www.cas.org/about-us"
    is_redistribution_allowed = False

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
        """
        from simmate.apps.pubchem.client import PubChemClient

        return PubChemClient.get_data_from_cas_number(cas_number)

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
        from simmate.apps.pubchem.client import PubChemClient

        cas_number = PubChemClient.get_cas_from_molecule(molecule)
        return cls.search_cas(
            cas_number=cas_number,
            backend="PubChem",
            force_update=force_update,
        )

    # -------------------------------------------------------------------------
