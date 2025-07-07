# -*- coding: utf-8 -*-

import gzip
import json
import logging
import urllib
from datetime import datetime
from pathlib import Path

import pandas
import requests
from django.utils.timezone import make_aware
from pymatgen.io.cif import CifFile
from rich.progress import track

from simmate.apps.rdkit.models import Molecule
from simmate.database.base_data_types import table_column
from simmate.toolkit import Molecule as ToolkitMolecule


class PdbLigand(Molecule):
    """
    Small molecules from the [Protein Data Bank (PDB)](https://www.wwpdb.org/).

    The small molecules are loaded from the "chemical component dictionary"
    at https://www.wwpdb.org/data/ccd. These molecules are also available as
    bulk downloads from http://ligand-expo.rcsb.org/ld-download.html
    """

    class Meta:
        db_table = "pdb__ligands"

    # disable cols
    source = None

    html_display_name = "PDB Ligands"
    html_description_short = (
        "Ligands (i.e. small molecules) found in the Protein Data Bank"
    )

    external_website = "https://www.wwpdb.org/"
    source_doi = "https://www.wwpdb.org/data/ccd"

    id = table_column.CharField(max_length=5, primary_key=True)
    """
    The id used to represent the molecule (ex: "ZZZ")
    """

    name = table_column.TextField()
    """
    Chemical name of the molecule. All names are converted to full lower-case
    """

    type_code = table_column.TextField()
    """
    A preliminary classification used by PDB (ex: "HETAIN")
    """
    # _chem_comp.pdbx_type

    type = table_column.TextField()
    """
    The type of monomer (ex: "NON-POLYMER")
    """
    # _chem_comp.type

    created_at = table_column.DateTimeField(
        blank=True,
        null=True,
        db_index=True,
    )
    """
    Timestamp of when this row was first added to the PDB database
    """
    # _chem_comp.pdbx_initial_date

    updated_at = table_column.DateTimeField(
        blank=True,
        null=True,
        db_index=True,
    )
    """
    Timestamp of when this row was was lasted changed / updated by the PDB database
    """
    # _chem_comp.pdbx_modified_date

    protein_ids = table_column.JSONField(blank=True, null=True)
    """
    List of PDB protein IDs where this ligand is found
    """
    # TODO: this should become a foreign key to PdbProtein table in the future

    @property
    def external_link(self) -> str:
        """
        URL to this molecule in the "PDB Europe" website.
        """
        # example URL for ligand: https://www.ebi.ac.uk/pdbe-srv/pdbechem/chemicalCompound/complete/123
        # example URL for protein: https://www.ebi.ac.uk/pdbe/entry/pdb/1gi5
        return f"https://www.ebi.ac.uk/pdbe-srv/pdbechem/chemicalCompound/complete/{self.id}"

    # -------------------------------------------------------------------------

    @classmethod
    def _load_data(cls):
        """
        This link gives directions for archive locations:

        - http://www.wwpdb.org/ftp/pdb-ftp-sites

        And it tells us (i) where all small molecules (ligands) are stored and (ii) a JSON file to download a list of all of the molecule IDs:

        i.  https://files.wwpdb.org/pub/pdb/refdata/chem_comp/
        ii. https://files.wwpdb.org/pub/pdb/holdings/refdata_id_list.json.gz

        The same is done for PDB files:

        i.  https://files.wwpdb.org/pub/pdb/data/structures/all/mmCIF/{pdb_id}.cif.gz  # <-- note the {}
        ii. https://files.wwpdb.org/pub/pdb/holdings/current_file_holdings.json.gz

        Because the chem_comp (ligands) is a much smaller dataset, they also provide a bulk
        download option instead of the links above:

        - https://www.wwpdb.org/data/ccd
        - https://files.wwpdb.org/pub/pdb/data/monomers/components.cif



        Separately, I found directions on downloading ligands that might be helpful in the future:

        1. Go to https://www.rcsb.org/docs/programmatic-access/file-download-services
        2. ctrl+F "ligand" to find the "Small molecule files" section
        3. select format type (but idk how to iterate...)

        There are also batch download scripts, but these look to be intended for full
        protein files, while we only want small molecules for now. I don't use these scripts
        but instead write my own:

        - https://www.rcsb.org/docs/programmatic-access/batch-downloads-with-shell-script



        #### 07.01.2025

        Looks like the Ligand Expo has been retired. I'm using these links now:
        - https://www.wwpdb.org/data/ccd
        - https://www.rcsb.org/search
        - https://data.rcsb.org/
        - https://github.com/rcsb/py-rcsb-api

        """
        # There is no need for refdata_id_list.json like we did for proteins bc
        # PDB provides a single bulk download file for us.

        # download, uncompress, and read the listing to a dictionary
        logging.info("Downloading ligands from PDB...")
        data_filename = Path("components.cif")
        if not data_filename.exists():
            data_url = "https://files.wwpdb.org/pub/pdb/data/monomers/components.cif"
            urllib.request.urlretrieve(data_url, data_filename)
        logging.info("Reading ligands file...")
        data = CifFile.from_file(data_filename).data

        logging.info("Downloading mappings from PDB...")
        # DEPREC - ligand expo no longer exists.
        # mapping_url = "http://ligand-expo.rcsb.org/dictionaries/cc-to-pdb.tdd"
        # mapping_filename = Path("cc-to-pdb.tdd")
        # if not mapping_filename.exists():
        #     urllib.request.urlretrieve(mapping_url, mapping_filename)
        # mappings = pandas.read_csv(
        #     mapping_filename,
        #     delimiter="\t",
        #     header=None,
        #     names=["ligand_id", "protein_ids"],
        #     index_col="ligand_id",
        # )
        # protein_ids = mappings.loc[ligand_id].protein_ids.strip().split(" ")
        data_filename = Path("cc_to_pdb_map.json")
        if data_filename.exists():
            with open(data_filename, "r") as f:
                pdb_id_map = json.load(f)
        else:
            ligand_ids = [e.data.get("_chem_comp.id", None) for k, e in data.items()]
            pdb_id_map = {
                ligand_id: cls._get_pdb_ids(ligand_id, silence_errors=True)
                for ligand_id in track(ligand_ids)
            }
            with open(data_filename, "w") as f:
                json.dump(pdb_id_map, f)

        # This for-loop simply loads all the metadata and smiles strings
        logging.info("Parsing metadata and molecules...")
        db_objs = []
        failed = 0
        for key, entry in track(data.items(), total=len(data)):
            # TODO: skip if molecule has already been added.
            # Maybe check the "last_modified" data too

            # ~30 of the 42k molecule fail to load because they don't have OpenEye
            # smiles listed. Another ~200 fail because of invalid smiles
            try:
                # convert CIF object to python dict
                entry_data = entry.data

                # This section grabs the SMILES string from the CIF file
                # and then converts to a Molecule.
                comp_ids = entry_data.get("_pdbx_chem_comp_descriptor.comp_id")
                descriptors = entry_data.get("_pdbx_chem_comp_descriptor.descriptor")
                programs = entry_data.get("_pdbx_chem_comp_descriptor.program")
                program_versions = entry_data.get(
                    "_pdbx_chem_comp_descriptor.program_version"
                )
                types = entry_data.get("_pdbx_chem_comp_descriptor.type")
                df = pandas.DataFrame(
                    data={
                        "comp_id": comp_ids,
                        "descriptor": descriptors,
                        "program": programs,
                        "program_version": program_versions,
                        "type": types,
                    }
                )
                smiles_row = df[
                    (df.type == "SMILES_CANONICAL")
                    & (df.program == "OpenEye OEToolkits")
                ].iloc[0]
                smiles_str = smiles_row.descriptor
                molecule = ToolkitMolecule.from_smiles(smiles_str)

                # pull timestamps and convert to proper format
                created_at = make_aware(
                    datetime.strptime(
                        entry_data.get("_chem_comp.pdbx_initial_date", None),
                        "%Y-%m-%d",
                    )
                )
                updated_at = make_aware(
                    datetime.strptime(
                        entry_data.get("_chem_comp.pdbx_modified_date", None),
                        "%Y-%m-%d",
                    )
                )

                # grab protein ids (and not all ligands have them)
                ligand_id = entry_data.get("_chem_comp.id", None)
                protein_ids = pdb_id_map.get(ligand_id, None)

                # now finalize the metadata and molecule into a database object
                db_obj = PdbLigand.from_toolkit(
                    molecule=molecule,
                    molecule_original=smiles_str,  # consider setting to mmCIF
                    is_3d=False,
                    # grab basic metadata
                    id=ligand_id,
                    type_code=entry_data.get("_chem_comp.pdbx_type", None),
                    type=entry_data.get("_chem_comp.type", None),
                    name=entry_data.get("_chem_comp.name", None),
                    created_at=created_at,
                    updated_at=updated_at,
                    protein_ids=protein_ids,
                )
                db_objs.append(db_obj)

            except:
                failed += 1

        logging.info("Saving new rows to database...")
        cls.objects.bulk_create(
            db_objs,
            batch_size=1000,
            ignore_conflicts=True,
        )

        logging.info("Adding molecule fingerprints...")
        cls.populate_fingerprint_database()

        logging.info("Done.")
        return failed

    @staticmethod
    def _get_pdb_ids(cc_id: str, silence_errors: bool = False):

        import urllib3

        # to silence ssl warnings below
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

        response = requests.post(url, json=query, verify=False)  # ssl disabled

        if response.ok:
            if response.status_code == 204:  # "No content" code
                return []
            data = response.json()
            pdb_ids = [result["identifier"] for result in data.get("result_set", [])]
            return pdb_ids
        else:
            if silence_errors:
                return None
            raise Exception(f"Request failed: {response.status_code}\n {response.text}")


# -----------------------------------------------------------------------------

# NOTE: this function is for loading proteins + metadata for when I want this
# as its own table. For now, I just use http://ligand-expo.rcsb.org/dictionaries/cc-to-pdb.tdd
# and store linked IDs. In the future this will be a foreign key field


def _load_pdb_proteins(
    id_listings_url: str = "https://files.wwpdb.org/pub/pdb/holdings/current_file_holdings.json.gz",
    # check_local_first: bool = True,  # TODO
):
    id_listings_url = (
        "https://files.wwpdb.org/pub/pdb/holdings/current_file_holdings.json.gz"
    )

    # download, uncompress, and read the listing to a dictionary
    logging.info("Loading list of available protein IDs...")

    local_filename = Path("current_file_holdings.json.gz")
    urllib.request.urlretrieve(id_listings_url, local_filename)

    with gzip.open(local_filename) as file:
        id_listings = json.load(file)

    logging.info("Done.")

    # TODO: if update_only=True, only include IDs that aren't in our database yet

    # grab all the URLs for downloading mmcif files from pdb
    mmcif_locs = [v["mmcif"][0] for k, v in id_listings.items()]

    base_url = "https://files.wwpdb.org/pub/"
    for mmcif_loc in track(mmcif_locs[:100]):
        full_url = base_url + mmcif_loc
        mmcif_file = Path(mmcif_loc).name
        urllib.request.urlretrieve(id_listings_url, mmcif_file)
        breakpoint()  # TODO -- load

        # delete file to saze on disk space
        mmcif_file.unlink()
