# -*- coding: utf-8 -*-

import logging
import shutil

import numpy
import pandas
from rich.progress import track

from simmate.apps.rdkit.models import Molecule
from simmate.configuration import settings
from simmate.database.base_data_types import table_column
from simmate.toolkit import Molecule as ToolkitMolecule
from simmate.utilities import download_file, get_directory


class ChemblMolecule(Molecule):
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

    html_display_name = "ChEMBL"
    html_description_short = (
        "a manually curated database of bioactive molecules with drug-like properties."
    )

    external_website = "https://www.ebi.ac.uk/chembl/beta/"
    source_doi = "https://doi.org/10.1093/nar/gky1075"
    is_redistribution_allowed = True

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

    molecule_type = table_column.CharField(max_length=25, blank=True, null=True)
    """
    Whether the entry is a small molecule, protein, gene, etc.
    """
    # TODO: change to choice field
    # Small molecule
    # Unknown
    # (NULL)
    # Protein
    # Antibody
    # Oligonucleotide
    # Enzyme
    # Gene
    # Oligiosacchride
    # Cell

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

    # -------------------------------------------------------------------------
    # There are the other columns from "compound_properties" table that I should
    # consider adding to the base Molecule table bc they can be easily calculated
    #
    # MW_FREEBASE		Molecular weight of parent compound
    # HBA		        Number hydrogen bond acceptors
    # HBD		        Number hydrogen bond donors
    # PSA		        Polar surface area
    # RTB		        Number rotatable bonds
    # FULL_MWT		    Molecular weight of the full compound including any salts
    # AROMATIC_RINGS	Number of aromatic rings
    # HEAVY_ATOMS		Number of heavy (non-hydrogen) atoms
    # MW_MONOISOTOPIC	Monoisotopic parent molecular weight
    # FULL_MOLFORMULA	Molecular formula for the full compound (including any salt)
    #
    # -------------------------------------------------------------------------

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

        For example:
            https://ftp.ebi.ac.uk/pub/databases/chembl/ChEMBLdb/latest/chembl_36_sqlite.tar.gz

        Once downloaded, unpacked the compressed file in to the
        ~/simmate/chembl/ directory where this method will pick it up.

        [See all options here](https://chembl.gitbook.io/chembl-interface-documentation/downloads)
        """
        import sqlite3

        database_file = cls.download_source_data()
        connection = sqlite3.connect(database_file)
        cursor = connection.cursor()

        logging.info("Pulling molecule data from ChEMBL db...")
        query = """
        SELECT
            S1.molregno,
            S1.canonical_smiles,
         	D1.chembl_id,
            D1.molecule_type,
            P1.qed_weighted,
            P1.alogp,
            P1.ro3_pass,
            P1.num_ro5_violations,
            P1.hba,
            P1.hbd,
            P1.np_likeness_score
        FROM
         	compound_structures S1
        LEFT JOIN 
        	molecule_dictionary D1
        	ON S1.molregno = D1.molregno
        LEFT JOIN 
        	compound_properties P1
        	ON S1.molregno = P1.molregno
        ORDER BY
            S1.molregno ASC
        """
        cursor.execute(query)

        data = pandas.DataFrame(
            data=cursor.fetchall(),  # .fetchmany(5000), for quick testing
            columns=[c[0] for c in cursor.description],
        )  # OPTIMIZE: consider fetchmany with for-loop

        # BUG-FIX (nan-->None)
        data = data.replace({numpy.nan: None})

        # In order to allow 'continuation' from paused loads, we remove
        # all IDs that are less than the max ID already in our database
        if cls.objects.exists():
            max_id = cls.objects.order_by("-id").values_list("id").first()[0]
            data = data[data["molregno"] > max_id]

        total = len(data)
        logging.info(f"{total} entries will be loaded into the database")

        # autopopulate database columns for each molecule (no saving yet)
        logging.info("Generating database objects...")
        failed_rows = []
        db_objs = []
        for i, entry in track(data.iterrows(), total=len(data)):

            try:
                molecule = ToolkitMolecule.from_smiles(entry.canonical_smiles)
                molecule_kwargs = cls.from_toolkit(
                    molecule=molecule,
                    is_invalid_molecule=False,
                    as_dict=True,
                )
            except:
                molecule_kwargs = {"is_invalid_molecule": True}

            # RO3 is given as Y, N, or (NULL) -- but we want a boolean
            if entry.ro3_pass == "Y":
                ro3_pass = True
            elif entry.ro3_pass == "N":
                ro3_pass = False
            else:
                ro3_pass = None

            # now convert the entry to a database object
            molecule_db = cls.from_toolkit(
                id=entry.molregno,
                molecule_original=entry.canonical_smiles,
                chembl_id=entry.chembl_id,
                molecule_type=entry.molecule_type,
                drug_likeness=entry.qed_weighted,
                alog_p_chembl=entry.alogp,
                rule_of_3_pass=ro3_pass,  # see fix above
                rule_of_5_violations=entry.num_ro5_violations,
                num_h_acceptors_lipinski=entry.hba,
                num_h_donors_lipinski=entry.hbd,
                natural_product_likeness=entry.np_likeness_score,
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
        cls.objects.bulk_create(
            db_objs,
            batch_size=1000,
            ignore_conflicts=True,
        )

        logging.info("Adding molecule fingerprints...")
        cls.populate_fingerprint_database()

        logging.info(f"Done! There are now {cls.objects.count()} molecules.")
        return failed_rows

    @classmethod
    def download_source_data(cls):

        target_dir = get_directory(settings.config_directory / "chembl")

        version = 36
        db_name = f"chembl_{version}"
        db_filename = target_dir / f"{db_name}.db"

        if db_filename.exists():
            return db_filename

        base_url = "https://ftp.ebi.ac.uk/pub/databases/chembl/ChEMBLdb/latest/"
        filename = f"{db_name}_sqlite.tar.gz"
        download_filename = target_dir / filename

        logging.info("Downloading ChEMBL db...")
        if not download_filename.exists():
            download_file(
                url=base_url + filename,
                dest_path=download_filename,
            )

        logging.info("Unpacking ChEMBL db...")
        shutil.unpack_archive(download_filename, target_dir)
        shutil.move(
            target_dir / db_name / f"{db_name}_sqlite" / db_filename.name,
            target_dir,
        )
        shutil.rmtree(target_dir / db_name)
        download_filename.unlink()

        logging.info("ChEMBL data ready.")
        return db_filename
