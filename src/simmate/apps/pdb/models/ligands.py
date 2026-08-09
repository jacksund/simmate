# -*- coding: utf-8 -*-

import json
import logging
import urllib
from datetime import datetime

import pandas
import requests
from django.utils.timezone import make_aware
from pymatgen.io.cif import CifFile
from rich.progress import track

from simmate.apps.rdkit.models import Molecule
from simmate.config import settings
from simmate.database.core import table_column
from simmate.database.mixins import ThirdPartyData
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

    id = table_column.CharField(max_length=5, primary_key=True)
    """The id used to represent the molecule (ex: "ZZZ")"""

    name = table_column.TextField()
    """Chemical name of the molecule."""

    type_code = table_column.TextField()
    """A preliminary classification used by PDB (ex: "HETAIN")"""

    monomer_type = table_column.TextField()
    """The type of monomer (ex: "NON-POLYMER")"""

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
        return f"https://www.ebi.ac.uk/pdbe-srv/pdbechem/chemicalCompound/complete/{self.id}"

    @classmethod
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

        # 1. Download and read the listing of all ligands
        data_filename = pdb_config_dir / "components.cif"
        if not data_filename.exists():
            logging.info("Downloading ligands from PDB...")
            data_url = "https://files.wwpdb.org/pub/pdb/data/monomers/components.cif"
            urllib.request.urlretrieve(data_url, data_filename)

        logging.info("Reading ligands file (this may take a minute)...")
        data = CifFile.from_file(data_filename).data

        # 2. Map ligands to the proteins they are found in
        # This is a VERY slow process if it hasn't been done before.
        map_filename = pdb_config_dir / "cc_to_pdb_map.json"
        if map_filename.exists():
            with open(map_filename, "r") as f:
                pdb_id_map = json.load(f)
        elif include_protein_ids:
            logging.info("Fetching ligand-to-protein mappings (this is slow)...")
            ligand_ids = [e.data.get("_chem_comp.id") for e in data.values()]
            pdb_id_map = {
                lid: cls._get_pdb_ids(lid, silence_errors=True)
                for lid in track(ligand_ids)
            }
            with open(map_filename, "w") as f:
                json.dump(pdb_id_map, f)
        else:
            pdb_id_map = {}

        # 3. Parse metadata and molecules
        logging.info("Parsing metadata and molecules...")
        db_objs = []
        failed = 0
        for entry in track(data.values()):
            try:
                # convert CIF object to python dict
                entry_data = entry.data

                # grab the SMILES string and convert to a Molecule.
                # All SMILES are stored in a table-like format in the CIF
                df = pandas.DataFrame(
                    data={
                        "type": entry_data.get("_pdbx_chem_comp_descriptor.type"),
                        "program": entry_data.get("_pdbx_chem_comp_descriptor.program"),
                        "smiles": entry_data.get(
                            "_pdbx_chem_comp_descriptor.descriptor"
                        ),
                    }
                )
                smiles_row = df[
                    (df.type == "SMILES_CANONICAL")
                    & (df.program == "OpenEye OEToolkits")
                ].iloc[0]
                smiles_str = smiles_row.smiles
                molecule = ToolkitMolecule.from_smiles(smiles_str)

                # pull timestamps and convert to proper format
                created_at_raw = entry_data.get("_chem_comp.pdbx_initial_date")
                updated_at_raw = entry_data.get("_chem_comp.pdbx_modified_date")
                created_at_original = (
                    make_aware(datetime.strptime(created_at_raw, "%Y-%m-%d"))
                    if created_at_raw
                    else None
                )
                updated_at_original = (
                    make_aware(datetime.strptime(updated_at_raw, "%Y-%m-%d"))
                    if updated_at_raw
                    else None
                )

                # finalize the metadata and molecule into a database object
                ligand_id = entry_data.get("_chem_comp.id")
                db_obj = PdbLigand.from_toolkit(
                    molecule=molecule,
                    molecule_original=smiles_str,
                    is_3d=False,
                    id=ligand_id,
                    type_code=entry_data.get("_chem_comp.pdbx_type"),
                    monomer_type=entry_data.get("_chem_comp.type"),
                    name=entry_data.get("_chem_comp.name"),
                    created_at_original=created_at_original,
                    updated_at_original=updated_at_original,
                    protein_ids_original=pdb_id_map.get(ligand_id),
                )
                db_objs.append(db_obj)
            except Exception:
                failed += 1

        # 4. Save to database
        logging.info(f"Saving {len(db_objs)} rows to database...")
        cls.objects.bulk_create(
            db_objs,
            batch_size=1000,
            ignore_conflicts=True,
        )
        if settings.postgres_rdkit_extension:
            cls.populate_fingerprint_database()
        logging.info("Done.")
        return failed

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
