# -*- coding: utf-8 -*-

import polars
from rich.progress import track

from simmate.apps.rdkit.models import Molecule
from simmate.config import settings
from simmate.database.core import table_column
from simmate.database.mixins import ThirdPartyData
from simmate.database.utils import batch_bulk_create
from simmate.toolkit import Molecule as ToolkitMolecule

from ..client import ChemblClient


class ChemblMolecule(ThirdPartyData, Molecule):
    """
    Molecules from the
    [ChEMBL database](https://chembl.gitbook.io/chembl-interface-documentation/downloads)
    database.

    Useful links:
    - https://ftp.ebi.ac.uk/pub/databases/chembl/ChEMBLdb/latest/
    - https://ftp.ebi.ac.uk/pub/databases/chembl/ChEMBLdb/latest/chembl_33_schema.png
    - https://ftp.ebi.ac.uk/pub/databases/chembl/ChEMBLdb/latest/schema_documentation.html

    ChEMBL distributes their database as manual downloads in a variety of
    formats, where we choose to use their SQLite download.

    [See all options here](https://chembl.gitbook.io/chembl-interface-documentation/downloads)
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
    @batch_bulk_create(batch_size=1_000)
    def load_source_data(cls, **kwargs):

        if not hasattr(cls, "_max_id"):
            cls._max_id = 0
            if cls.objects.exists():
                cls._max_id = cls.objects.order_by("-id").values_list("id").first()[0]

        for df in ChemblClient.get_molecule_data(chunk_size=10_000):
            df = df.filter(polars.col("molregno") > cls._max_id)

            for row in track(df.iter_rows(named=True), total=len(df)):
                try:
                    molecule = ToolkitMolecule.from_smiles(row["canonical_smiles"])
                    molecule_kwargs = cls.from_toolkit(
                        molecule=molecule,
                        is_invalid_molecule=False,
                        as_dict=True,
                    )
                except Exception:
                    molecule_kwargs = {"is_invalid_molecule": True}

                if row["ro3_pass"] == "Y":
                    ro3_pass = True
                elif row["ro3_pass"] == "N":
                    ro3_pass = False
                else:
                    ro3_pass = None

                yield cls.from_toolkit(
                    id=row["molregno"],
                    molecule_original=row["canonical_smiles"],
                    chembl_id=row["chembl_id"],
                    molecule_type=row["molecule_type"],
                    drug_likeness=row["qed_weighted"],
                    alog_p_chembl=row["alogp"],
                    rule_of_3_pass=ro3_pass,
                    rule_of_5_violations=row["num_ro5_violations"],
                    num_h_acceptors_lipinski=row["hba"],
                    num_h_donors_lipinski=row["hbd"],
                    natural_product_likeness=row["np_likeness_score"],
                    **molecule_kwargs,
                )

        if settings.postgres_rdkit_extension:
            cls.populate_fingerprint_database()
