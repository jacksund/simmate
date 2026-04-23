# -*- coding: utf-8 -*-

from simmate.apps.rdkit.models import Molecule
from simmate.database.core import table_column
from simmate.database.mixins import ThirdPartyData

from ..client import CasRegistryClient
from ..utils import validate_cas_number


class CasRegistryMolecule(ThirdPartyData, Molecule):
    """
    Molecules & Compounds from the
    [CAS Common Chemistry database](https://www.cas.org/about-us)
    database.

    This table is built to load "lazily" using the official CAS Registry API.
    Specifically, the full dataset is not loaded up front. Instead, only when
    a CAS number or molecule is requested, then it is pulled from the API
    before being loaded into this table.

    CAS Common Chemistry:
        - Web UI search: https://commonchemistry.cas.org/
        - API: https://commonchemistry.cas.org/api-overview
        - (no bulk downloads available without purchase)
        - Extra info: https://www.cas.org/services/commonchemistry-api
    """

    class Meta:
        db_table = "cas_registry__molecules"

    external_website = "https://www.cas.org/about-us"
    is_redistribution_allowed = False

    id = table_column.CharField(max_length=15, primary_key=True)
    """
    The CAS Registry Number used to represent the compound (ex: "1039987-26-2")
    """

    common_name = table_column.TextField(blank=True, null=True)
    """
    The name of this compound that is used most often. This pulls from the
    CAS Registry's page header.
    """

    @property
    def external_link(self) -> str:
        """
        URL to this molecule in the CAS website.
        """
        # ex: https://commonchemistry.cas.org/detail?cas_rn=1039987-26-2
        return f"https://commonchemistry.cas.org/detail?cas_rn={self.id}"

    @classmethod
    def search_cas(
        cls,
        cas_number: str,
        force_update: bool = False,
    ):
        """
        Searches the database for a CAS Registry Number. If it's not found,
        it queries the official CAS API, loads the data, and saves it to the
        database for future use.

        Args:
            cas_number (str): The CAS RN to search for (e.g. "1039987-26-2").
            force_update (bool): Whether to ignore the database and force a
                fresh API query. Defaults to False.

        Returns:
            CasRegistryMolecule: The database entry for the CAS number.
        """
        if not force_update:
            # check the database to see if this has been searched for
            if cls.objects.filter(id=cas_number).exists():
                return cls.objects.get(id=cas_number)

        is_valid = validate_cas_number(cas_number)
        if not is_valid:
            raise Exception(f"{cas_number} is not a valid CAS number")

        # search official api
        data = CasRegistryClient.detail(cas_number)
        official_data = {
            "id": data["rn"],
            "common_name": data.get("name"),
            "molecule": data.get("molecule_obj"),
        }

        # we use update_or_create to avoid race conditions when creating
        cas_entry, is_new = cls.objects.update_or_create(
            id=cas_number,
            defaults=cls.from_toolkit(
                **official_data,
                as_dict=True,
            ),
        )

        # ensure the fingerprint is added
        cls.populate_fingerprint_database()

        return cas_entry

    @classmethod
    def search_molecule(
        cls,
        molecule: Molecule,
        force_update: bool = False,
    ):
        """
        Searches the database for a molecule. If it's not found, it queries the
        official CAS API (via InChIKey), retrieves the first matching CAS number,
        and then calls `search_cas` to load the full details.

        Args:
            molecule (Molecule): The molecule to search for.
            force_update (bool): Whether to ignore the database and force a
                fresh API query. Defaults to False.

        Returns:
            CasRegistryMolecule: The database entry for the molecule.
        """
        inchi_key = molecule.to_inchi_key()

        if not force_update:
            # check the database to see if this has been searched for
            if cls.objects.filter(inchi_key=inchi_key).exists():
                return cls.objects.get(inchi_key=inchi_key)

        # Otherwise we need to search official api
        # The client's search method is robust and handles SMILES, InChI, etc.
        # We start with InChIKey as it is most specific.
        search_results = CasRegistryClient.search(f"InChIKey={inchi_key}", size=1)
        results = search_results.get("results", [])

        if not results:
            return None

        cas_number = results[0]["rn"]
        return cls.search_cas(cas_number)
