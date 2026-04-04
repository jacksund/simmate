# -*- coding: utf-8 -*-

import logging

from rich.progress import track

from simmate.apps.rdkit.models import Molecule
from simmate.database.core import table_column
from simmate.database.mixins import ThirdPartyData
from simmate.toolkit import Molecule as ToolkitMolecule
from simmate.config import settings
import polars

from .client import ChemblClient


class ChemblMolecule(ThirdPartyData, Molecule):
    """
    Molecules from the
    [ChEMBL database](https://chembl.gitbook.io/chembl-interface-documentation/downloads)
    database.

    Useful links:
    - https://ftp.ebi.ac.uk/pub/databases/chembl/ChEMBLdb/latest/
    - https://ftp.ebi.ac.uk/pub/databases/chembl/ChEMBLdb/latest/chembl_33_schema.png
    - https://ftp.ebi.ac.uk/pub/databases/chembl/ChEMBLdb/latest/schema_documentation.html
    """

    class Meta:
        db_table = "chembl__molecules"

    external_website = "https://www.ebi.ac.uk/chembl/beta/"
    source_doi = "https://doi.org/10.1093/nar/gky1075"
    is_redistribution_allowed = True

    remote_archive_link = "https://archives.simmate.org/ChemblMolecule-2026-03-22.zip"
    archive_fields = [
        "chembl_id",
        "is_invalid_molecule",
        "molecule_type",
        "drug_likeness",
        "alog_p_chembl",
        "rule_of_3_pass",
        "rule_of_5_violations",
        "num_h_acceptors_lipinski",
        "num_h_donors_lipinski",
        "natural_product_likeness",
    ]

    # id is set to the 'molregno' in the chembl db (ex: 12345)

    chembl_id = table_column.CharField(max_length=25, blank=True, null=True)
    """
    The id used to represent the molecule (ex: "CHEMBL3183843"). 
    
    Note, this is NOT the primary key. Instead, we use 'molregno' which is 
    chembl's internal identifer and often their own primary key too.
    """

    is_invalid_molecule = table_column.BooleanField(blank=True, null=True)
    """
    whether the molecule was loaded successfully into the simmate database
    """
    
    molecule_type_options = [
        "Small molecule",
        "Unknown",
        "(NULL)",
        "Protein",
        "Antibody",
        "Oligonucleotide",
        "Enzyme",
        "Gene",
        "Oligiosacchride",
        "Cell",
    ]
    molecule_type = table_column.CharField(max_length=25, blank=True, null=True)
    """
    Whether the entry is a small molecule, protein, gene, etc.
    """

    drug_likeness = table_column.FloatField(blank=True, null=True)
    """
    Weighted quantitative estimate of drug likeness (as defined by Bickerton et al., Nature Chem 2012)
    """
    # QED_WEIGHTED

    alog_p_chembl = table_column.FloatField(blank=True, null=True)
    """
    Calculated ALogP reported by ChEMBL
    """
    # ALOGP

    rule_of_3_pass = table_column.BooleanField(blank=True, null=True)
    """
    Indicates whether the compound passes the rule-of-three (mw < 300, logP < 3 etc)
    """
    # RO3_PASS

    rule_of_5_violations = table_column.IntegerField(blank=True, null=True)
    """
    Number of violations of Lipinski's rule-of-five, using HBA and HBD definitions
    """
    # NUM_RO5_VIOLATIONS

    num_h_acceptors_lipinski = table_column.IntegerField(blank=True, null=True)
    """
    Number of hydrogen bond acceptors calculated according to Lipinski's original 
    rules (i.e., N + O count))
    """
    # HBA_LIPINSKI

    num_h_donors_lipinski = table_column.IntegerField(blank=True, null=True)
    """
    Number of hydrogen bond donors calculated according to Lipinski's original 
    rules (i.e., NH + OH count)
    """
    # HBD_LIPINSKI

    natural_product_likeness = table_column.FloatField(blank=True, null=True)
    """
    Natural Product-likeness Score: Peter Ertl, Silvio Roggo, and Ansgar 
    Schuffenhauer Journal of Chemical Information and Modeling, 48, 68-74 (2008)
    """
    # NP_LIKENESS_SCORE

    @property
    def external_link(self) -> str:
        """
        URL to this molecule in the ChEMBL website.
        """
        # other API endpoints are outlined here:
        # https://chembl.gitbook.io/chembl-interface-documentation/web-services/chembl-data-web-services
        # ex: https://www.ebi.ac.uk/chembl/compound_report_card/CHEMBL3183843/
        return f"https://www.ebi.ac.uk/chembl/compound_report_card/{self.id}/"

    @classmethod
    def load_source_data(cls):
        """
        Only use this function if you are part of the Simmate dev team!
        Users should instead access data via the load_remote_archive method.

        Loads all structures directly for the ChEMBL database into the local
        Simmate database.

        ChEMBL distributes their database as manual downloads in a variety of
        formats, where we choose to use their SQLite download.

        [See all options here](https://chembl.gitbook.io/chembl-interface-documentation/downloads)
        """

        # In order to allow 'continuation' from paused loads, we remove
        # all IDs that are less than the max ID already in our database
        max_id = 0
        if cls.objects.exists():
            max_id = cls.objects.order_by("-id").values_list("id").first()[0]

        for df in ChemblClient.get_molecule_data(chunk_size=10_000):
            
            # filter down dataframe for the database model population
            df_model = df.filter(polars.col("molregno") > max_id)
            if df_model.is_empty():
                continue

            # autopopulate database columns for each molecule (no saving yet)
            logging.info(f"Generating and saving {len(df_model)} database objects...")
            db_objs = []
            for entry in track(df_model.iter_rows(named=True), total=len(df_model)):

                try:
                    molecule = ToolkitMolecule.from_smiles(entry["canonical_smiles"])
                    molecule_kwargs = cls.from_toolkit(
                        molecule=molecule,
                        is_invalid_molecule=False,
                        as_dict=True,
                    )
                except:
                    molecule_kwargs = {"is_invalid_molecule": True}

                # RO3 is given as Y, N, or (NULL) -- but we want a boolean
                if entry["ro3_pass"] == "Y":
                    ro3_pass = True
                elif entry["ro3_pass"] == "N":
                    ro3_pass = False
                else:
                    ro3_pass = None

                # now convert the entry to a database object
                molecule_db = cls.from_toolkit(
                    id=entry["molregno"],
                    molecule_original=entry["canonical_smiles"],
                    chembl_id=entry["chembl_id"],
                    molecule_type=entry["molecule_type"],
                    drug_likeness=entry["qed_weighted"],
                    alog_p_chembl=entry["alogp"],
                    rule_of_3_pass=ro3_pass,  # see fix above
                    rule_of_5_violations=entry["num_ro5_violations"],
                    num_h_acceptors_lipinski=entry["hba"],
                    num_h_donors_lipinski=entry["hbd"],
                    natural_product_likeness=entry["np_likeness_score"],
                    **molecule_kwargs,
                )
                db_objs.append(molecule_db)

                # save every time we have 1000 structures
                if len(db_objs) >= 1000:
                    cls.objects.bulk_create(
                        db_objs,
                        batch_size=1000,
                        ignore_conflicts=True,
                    )
                    db_objs = []  # reset for next batch

            # one last save in case we exited the loop above with
            # remaining structures
            if db_objs:
                cls.objects.bulk_create(
                    db_objs,
                    batch_size=1000,
                    ignore_conflicts=True,
                )

        logging.info("Adding molecule fingerprints...")
        if settings.postgres_rdkit_extension:
            cls.populate_fingerprint_database()

        logging.info("Done!")
