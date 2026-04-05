# -*- coding: utf-8 -*-

import logging

import polars
from rich.progress import track

from simmate.database.core import DatabaseTable, table_column
from simmate.database.utils import batch_bulk_create

from ..client import ChemblClient
from .document import ChemblDocument
from .molecules import ChemblMolecule


class ChemblAssayResult(DatabaseTable):
    """
    Assay results from the ChEMBL database. This data is pulled primarily from
    the "activities" table and also pulls/flattens related information such
    as from the "assays" table.

    From the Chembl docs...
        - activities table: Activity 'values' or 'end points' that are the results
          of an assay recorded in a scientific document. Each activity is
          described by a row.
        - assays table: Table storing a list of the assays that are reported in each
          document. Similar assays from different publications will appear as
          distinct assays in this table.
    """

    class Meta:
        db_table = "chembl__assay_results"

    chembl_document = table_column.ForeignKey(
        ChemblDocument,
        on_delete=table_column.PROTECT,
        blank=True,
        null=True,
        related_name="chembl_assay_results",
    )
    """
    Document that this assay result was extracted from
    """

    chembl_compound = table_column.ForeignKey(
        ChemblMolecule,
        on_delete=table_column.PROTECT,
        blank=True,
        null=True,
        related_name="chembl_assay_results",
    )
    """
    Molecular Compound that was tested in this assay
    """

    value_relation = table_column.TextField(blank=True, null=True)
    """
    Symbol constraining the activity value (e.g. >, <, =)
    """

    value = table_column.FloatField(blank=True, null=True)
    """
    Datapoint "result" value for the assay
    """

    value_units = table_column.TextField(blank=True, null=True)
    """
	Selected 'Standard' units for data type: e.g. concentrations are in nM.
    """

    data_validity_check = table_column.BooleanField(blank=True, null=True)
    """
    Shows whether the standardised columns have been curated/set (True) or just 
    default to the published data (False).
    """

    value_type = table_column.TextField(blank=True, null=True)
    """
    Standardised version of the published value type 
    (e.g. IC50 rather than Ic-50/Ic50/ic50/ic-50)
    """

    activity_comment = table_column.TextField(blank=True, null=True)
    """
    Previously used to report non-numeric activities i.e. 'Slighty active', 
    'Not determined'.
    """
    # Chembl note: STANDARD_TEXT_VALUE will be used for this in future, and
    # this will be just for additional comments.

    data_validity_comment = table_column.TextField(blank=True, null=True)
    """
    Comment reflecting whether the values for this activity measurement are 
    likely to be correct - one of 'Manually validated' (checked original paper 
    and value is correct), 'Potential author error' (value looks incorrect but 
    is as reported in the original paper), 'Outside typical range' (value seems 
    too high/low to be correct e.g., negative IC50 value), 'Non standard unit 
    type' (units look incorrect for this activity type).
    """

    is_potential_duplicate = table_column.BooleanField(blank=True, null=True)
    """
    When set to True, indicates that the value is likely to be a repeat citation 
    of a value reported in a previous ChEMBL paper, rather than a new, 
    independent measurement. Note: value of zero does not guarantee that the 
    measurement is novel/independent though
    """

    value_range_max = table_column.FloatField(blank=True, null=True)
    """
    Where the activity is a range, this represents the standardised version of
    the highest value of the range (with the lower value represented by STANDARD_VALUE)
    """

    value_text = table_column.TextField(blank=True, null=True)
    """
    Additional information about the measurement
    """

    mode_of_action_type = table_column.TextField(blank=True, null=True)
    """
    specifies the effect of the compound on its target
    """

    description = table_column.TextField(blank=True, null=True)
    """
    Description of the reported assay
    """

    target_organism = table_column.TextField(blank=True, null=True)
    """
    Name of the organism for the assay system (e.g., the organism, tissue or 
    cell line in which an assay was performed). May differ from the target 
    organism (e.g., for a human protein expressed in non-human cells, or 
    pathogen-infected human cells).
    """

    confidence_score = table_column.IntegerField(blank=True, null=True)
    """
    Confidence score, indicating how accurately the assigned target(s) 
    represents the actually assay target.
    0 means uncurated/unassigned, 1 = low confidence to 9 = high confidence.
    """

    assay_type = table_column.TextField(blank=True, null=True)
    """
    Description of assay type
    """

    assay_type_standard = table_column.TextField(blank=True, null=True)
    """
    Refers to an official BioAssay Ontology (based on value_type)
    """

    @classmethod
    @batch_bulk_create(batch_size=1_000)
    def load_source_data(cls, update_only: bool = False, limit: int = None, **kwargs):
        """
        Downloads the ChEMBL SQLite database and loads assay result data into
        the Simmate database.
        """
        if update_only and cls.objects.exists():
            logging.info("Checking last update...")
            min_activity_id = str(
                cls.objects.order_by("-id").values_list("id").first()[0]
            )
        else:
            min_activity_id = -1

        if not hasattr(cls, "_doc_ids"):
            logging.info("Filtering for existing IDs...")
            cls._doc_ids = set(
                ChemblDocument.objects.values_list("id", flat=True).all()
            )
            cls._mol_ids = set(
                ChemblMolecule.objects.values_list("id", flat=True).all()
            )

        chunks = ChemblClient.get_assay_result_data(
            min_activity_id=min_activity_id,
            chunk_size=250_000,
            limit=limit,
        )

        for df in chunks:
            df = df.filter(
                polars.col("doc_id").is_in(cls._doc_ids)
                & polars.col("molregno").is_in(cls._mol_ids)
            )
            for row in track(df.iter_rows(named=True), total=len(df)):
                yield cls(
                    id=row["activity_id"],
                    chembl_document_id=row["doc_id"],
                    chembl_compound_id=row["molregno"],
                    value_relation=row["standard_relation"],
                    value=row["standard_value"],
                    value_units=row["standard_units"],
                    data_validity_check=bool(row["standard_flag"]),
                    value_type=row["standard_type"],
                    activity_comment=row["activity_comment"],
                    data_validity_comment=row["data_validity_comment"],
                    is_potential_duplicate=bool(row["potential_duplicate"]),
                    value_range_max=row["standard_upper_value"],
                    value_text=row["standard_text_value"],
                    mode_of_action_type=row["action_type"],
                    description=row["assay_description"],
                    target_organism=row["assay_organism"],
                    confidence_score=row["confidence_score"],
                    assay_type=row["assay_type_description"],
                    assay_type_standard=row["bao_type"],
                )

        if hasattr(cls, "_doc_ids"):
            del cls._doc_ids
            del cls._mol_ids
