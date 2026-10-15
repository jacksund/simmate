# -*- coding: utf-8 -*-

import json
import logging
import urllib.request
from datetime import datetime
from pathlib import Path

import requests
from django.utils.timezone import make_aware
from pymatgen.io.cif import CifBlock
from rich.progress import track

from simmate.apps.rdkit.models import Molecule
from simmate.config import settings
from simmate.database.core import table_column
from simmate.database.mixins import ThirdPartyData
from simmate.database.utils import batch_bulk_create
from simmate.toolkit import Molecule as ToolkitMolecule


class PdbLigand(ThirdPartyData, Molecule):
    """
    Small molecules from the [Protein Data Bank (PDB)](https://www.wwpdb.org/).

    The small molecules are loaded from the "chemical component dictionary"
    at https://www.wwpdb.org/data/ccd.
    """

    class Meta:
        db_table = "pdb__ligands"

    external_website = "https://www.wwpdb.org/"
    source_doi = "https://www.wwpdb.org/data/ccd"
    is_redistribution_allowed = True

    remote_archive_link = (
        "https://assets.simmate.org/pdb/archive/PdbLigand-minimal-2026-10-14.csv.zip"
    )
    archive_fields = [
        "name",
        "type_code",
        "monomer_type",
        "is_delisted",
        "replaced_by",
        "is_invalid_molecule",
        "created_at_original",
        "updated_at_original",
        "protein_ids_original",
        # to keep size down
        "--created_at",
        "--updated_at",
    ]

    id = table_column.CharField(max_length=5, primary_key=True)
    """The id used to represent the molecule (ex: "ZZZ")"""

    name = table_column.TextField()
    """Chemical name of the molecule."""

    substance = table_column.ForeignKey(
        "inventory_management.Substance",
        on_delete=table_column.SET_NULL,
        related_name="pdb_entries",
        blank=True,
        null=True,
    )
    """
    The registered substance that this entry corresponds to, if any.
    """

    type_code = table_column.TextField(blank=True, null=True)
    """A preliminary classification used by PDB (ex: "HETAIN")"""

    monomer_type = table_column.TextField(blank=True, null=True)
    """The type of monomer (ex: "NON-POLYMER")"""

    is_invalid_molecule = table_column.BooleanField(blank=True, null=True)
    """
    Whether the molecule failed to load into the Simmate database. Invalid
    molecules may be missing a SMILES string or have issues with structure
    processing.
    """

    is_delisted = table_column.BooleanField(blank=True, null=True, default=False)
    """
    Whether the PDB has retired this ligand (a release status of "OBS" for
    "obsolete" in the PDB). The ID is kept in place and is never reused.

    Active entries have a release status of "REL" for "released".
    """

    replaced_by = table_column.CharField(max_length=5, blank=True, null=True)
    """
    For delisted ligands, the PDB ID of the ligand that replaces this one
    (if any).
    """

    created_at_original = table_column.DateTimeField(
        blank=True, null=True, db_index=True
    )
    """Timestamp of when this row was first added to the PDB database"""

    updated_at_original = table_column.DateTimeField(
        blank=True, null=True, db_index=True
    )
    """Timestamp of when this row was was lasted changed / updated by the PDB"""

    protein_ids_original = table_column.JSONField(blank=True, null=True)
    """List of PDB protein IDs where this ligand is found"""

    @property
    def external_link(self) -> str:
        return f"https://www.rcsb.org/ligand/{self.id}"

    # -------------------------------------------------------------------------

    @classmethod
    @batch_bulk_create(batch_size=1_000)
    def load_source_data(cls, include_protein_ids: bool = False):
        """
        Downloads and loads all ligand data from the PDB.

        #### Parameters

        - `include_protein_ids`: whether to fetch the list of PDB protein IDs
            where each ligand is found. This is a VERY slow process as it
            requires a separate API call for every ligand. Defaults to False.
        """

        # Ensure the config directory exists
        pdb_config_dir = settings.config_directory / "pdb"
        pdb_config_dir.mkdir(parents=True, exist_ok=True)

        # 1. Download the listing of all ligands
        data_filename = pdb_config_dir / "components.cif"
        if not data_filename.exists():
            logging.info("Downloading ligands from PDB...")
            data_url = "https://files.wwpdb.org/pub/pdb/data/monomers/components.cif"
            urllib.request.urlretrieve(data_url, data_filename)

        # 2. Map ligands to the proteins they are found in
        # This is a VERY slow process if it hasn't been done before.
        map_filename = pdb_config_dir / "cc_to_pdb_map.json"
        if map_filename.exists():
            with map_filename.open() as f:
                pdb_id_map = json.load(f)
        elif include_protein_ids:
            logging.info("Fetching ligand-to-protein mappings (this is slow)...")
            with data_filename.open() as f:
                ligand_ids = [
                    line[5:].strip() for line in f if line.startswith("data_")
                ]
            pdb_id_map = {
                lid: cls._get_pdb_ids(lid, silence_errors=True)
                for lid in track(ligand_ids)
            }
            with map_filename.open("w") as f:
                json.dump(pdb_id_map, f)
        else:
            pdb_id_map = {}

        # 3. Parse metadata and molecules
        logging.info("Parsing metadata and molecules...")
        for entry_data in track(cls._iter_cif_blocks(data_filename)):

            smiles_str = cls._get_smiles(entry_data)
            try:
                molecule = ToolkitMolecule.from_smiles(smiles_str)
                molecule_kwargs = cls.from_toolkit(
                    molecule=molecule,
                    is_3d=False,
                    is_invalid_molecule=False,
                    as_dict=True,
                )
            except Exception:
                molecule_kwargs = {"is_invalid_molecule": True}

            ligand_id = entry_data["_chem_comp.id"]
            yield cls.from_toolkit(
                id=ligand_id,
                molecule_original=smiles_str,
                type_code=_clean(entry_data.get("_chem_comp.pdbx_type")),
                monomer_type=_clean(entry_data.get("_chem_comp.type")),
                name=_clean(entry_data.get("_chem_comp.name")),
                is_delisted=(entry_data.get("_chem_comp.pdbx_release_status") == "OBS"),
                replaced_by=_clean(entry_data.get("_chem_comp.pdbx_replaced_by")),
                created_at_original=_parse_date(
                    entry_data.get("_chem_comp.pdbx_initial_date")
                ),
                updated_at_original=_parse_date(
                    entry_data.get("_chem_comp.pdbx_modified_date")
                ),
                protein_ids_original=pdb_id_map.get(ligand_id),
                **molecule_kwargs,
            )

        if settings.postgres_rdkit_extension:
            cls.populate_fingerprint_database()

    @staticmethod
    def _iter_cif_blocks(filename: Path):
        """
        Streams the (very large) CIF file one `data_` block at a time and
        yields each block as a dictionary. This avoids loading the entire
        file into memory at once.
        """
        lines = []
        with filename.open() as f:
            for line in f:
                if line.startswith("data_") and lines:
                    yield CifBlock.from_str("".join(lines)).data
                    lines = []
                lines.append(line)
        if lines:
            yield CifBlock.from_str("".join(lines)).data

    @staticmethod
    def _get_smiles(entry_data: dict) -> str | None:
        """
        Grabs the best available SMILES string from a CIF block. All
        descriptors are stored in a table-like format in the CIF, so we
        check in order of preference.
        """
        types = entry_data.get("_pdbx_chem_comp_descriptor.type", [])
        programs = entry_data.get("_pdbx_chem_comp_descriptor.program", [])
        descriptors = entry_data.get("_pdbx_chem_comp_descriptor.descriptor", [])

        # single-row tables are given as strings rather than lists
        if isinstance(types, str):
            types, programs, descriptors = [types], [programs], [descriptors]

        rows = list(zip(types, programs, descriptors))
        preferences = [
            ("SMILES_CANONICAL", "OpenEye OEToolkits"),
            ("SMILES_CANONICAL", "CACTVS"),
            ("SMILES", None),
        ]
        for target_type, target_program in preferences:
            for row_type, row_program, smiles in rows:
                if row_type == target_type and target_program in (None, row_program):
                    return smiles
        return None

    @staticmethod
    def _get_pdb_ids(cc_id: str, silence_errors: bool = False):
        """
        Queries the RCSB Search API to find all PDB entries that contain
        the given chemical component (ligand) ID.
        """
        # disable ssl warnings just in case the server has issues
        import urllib3

        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        url = "https://search.rcsb.org/rcsbsearch/v2/query"
        query = {
            "query": {
                "type": "terminal",
                "service": "text_chem",
                "parameters": {
                    "attribute": "rcsb_chem_comp_container_identifiers.comp_id",
                    "operator": "in",
                    "negation": False,
                    "value": [cc_id],
                },
            },
            "return_type": "entry",
        }
        response = requests.post(url, json=query, verify=False)
        if response.ok:
            if response.status_code == 204:  # "No content" code
                return []
            data = response.json()
            return [result["identifier"] for result in data.get("result_set", [])]
        elif silence_errors:
            return None
        else:
            response.raise_for_status()


def _clean(value: str | None) -> str | None:
    """Converts CIF null values ("?" and ".") to None."""
    return None if value in (None, "?", ".") else value


def _parse_date(value: str | None) -> datetime | None:
    """Converts a CIF date (ex: "2010-04-27") to a timezone-aware datetime."""
    value = _clean(value)
    return make_aware(datetime.strptime(value, "%Y-%m-%d")) if value else None
