import logging

import requests

from simmate.config import settings
from simmate.toolkit import Molecule


class CasRegistryClient:
    """
    A client for the CAS Common Chemistry API.
    API Overview: https://commonchemistry.cas.org/api-overview
    """

    base_url = "https://commonchemistry.cas.org/api"
    headers = {"X-API-KEY": settings.cas_registry.api_key}

    # -------------------------------------------------------------------------

    @classmethod
    def search(
        cls,
        query: str,
        size: int = 10,
        offset: int = 0,
    ) -> dict:
        """
        Search for chemical substances by name, CAS RN, SMILES, InChI, or InChIKey.
        """
        params = {"q": query, "size": size, "offset": offset}
        response = requests.get(
            f"{cls.base_url}/search", params=params, headers=cls.headers
        )
        response.raise_for_status()
        return response.json()

    @classmethod
    def detail(
        cls,
        cas_rn: str,
        include_molecule: bool = True,
    ) -> dict:
        """
        Retrieve all available information for a known CAS Registry Number.
        """
        params = {"cas_rn": cas_rn}
        response = requests.get(
            f"{cls.base_url}/detail", params=params, headers=cls.headers
        )
        response.raise_for_status()
        data = response.json()

        if include_molecule and "smiles" in data:
            data["molecule_obj"] = Molecule.from_smiles(data["smiles"])

        return data

    @classmethod
    def export(
        cls,
        cas_rn: str = None,
        uri: str = None,
        include_molecule: bool = True,
    ) -> dict:
        """
        Export substance data and return a dictionary containing the raw molfile
        string and a Simmate Molecule object.
        """
        if not uri and cas_rn:
            uri = f"http://commonchemistry.cas.org/detail?cas_rn={cas_rn}"

        params = {"uri": uri}
        response = requests.get(
            f"{cls.base_url}/export", params=params, headers=cls.headers
        )
        response.raise_for_status()

        mol_str = response.text
        data = {"molfile_str": mol_str}

        if include_molecule:
            # Note: We pass the string directly to the SDF parser
            data["molecule_obj"] = Molecule.from_sdf(mol_str)

        return data

    # -------------------------------------------------------------------------

    @classmethod
    def detail_from_search(cls, query: str, include_molecule: bool = True) -> dict:
        """
        Convenience method that searches for a term and returns the
        full detail for the first matching result.
        """
        search_results = cls.search(query, size=1)
        results = search_results.get("results", [])

        if not results:
            logging.warning(f"No results found for query: {query}")
            return None

        cas_rn = results[0]["rn"]
        return cls.detail(cas_rn, include_molecule=include_molecule)
