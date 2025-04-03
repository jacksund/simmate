# -*- coding: utf-8 -*-

import logging
from pathlib import Path

import numpy
import pandas
from rich.progress import track

from simmate.database.base_data_types import DatabaseTable, table_column

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
    def _load_data(
        cls,
        database_file: str | Path = "chembl_33.db",
        update_only: bool = False,
        limit: int = 250_000,  # very large table so we limit by default
    ):
        """
        Only use this function if you are part of the Simmate dev team!
        Users should instead access data via the load_remote_archive method.

        Loads all structures directly for the ChEMBL database into the local
        Simmate database.

        ChEMBL distributes their database as manual downloads in a variety of
        formats, where we choose to use their SQLite download.

        [See all options here](https://chembl.gitbook.io/chembl-interface-documentation/downloads)
        """
        import sqlite3

        # if we are only updating, grab the highest activity id to use as our
        # starting point.
        if update_only and cls.objects.exists():
            logging.info("Checking last update...")
            min_activity_id = str(
                cls.objects.order_by("-id")  # aka activity_id
                .values_list("id")
                .first()[0]
            )
        else:
            min_activity_id = -1

        connection = sqlite3.connect(database_file)
        cursor = connection.cursor()
        query = f"""
            SELECT
              a1.activity_id,
              a1.doc_id,
              a1.molregno,
              a1.standard_relation,
              a1.standard_value,
              a1.standard_units,
              a1.standard_flag,
              a1.standard_type,
              a1.activity_comment,
              a1.data_validity_comment,
              a1.potential_duplicate,
              a1.standard_upper_value,
              a1.standard_text_value,
              a1.action_type,
              a2.description as assay_description,
              a2.assay_organism,
              a2.confidence_score,
              a3.assay_desc as assay_type_description,
              b4.label as bao_type
            FROM
              activities a1
            LEFT JOIN
              assays a2
            	ON
            	a1.assay_id = a2.assay_id
            LEFT JOIN
              assay_type a3
            	ON
            	a2.assay_type = a3.assay_type
            LEFT JOIN
              bioassay_ontology b4
            	ON
            	a2.bao_format = b4.bao_id
            WHERE activity_id > {min_activity_id}
            ORDER BY a1.activity_id
            LIMIT {limit}
        """

        cursor.execute(query)

        data = pandas.DataFrame(
            data=cursor.fetchall(),
            columns=[c[0] for c in cursor.description],
        )  # OPTIMIZE: consider fetchmany with for-loop

        # BUG-FIX (nan-->None)
        data = data.replace({numpy.nan: None})

        # convert to dictionaries
        data = data.to_dict(orient="records")

        # autopopulate database columns for each molecule (no saving yet)
        logging.info("Generating database objects...")
        failed_rows = []
        for entry in track(data):
            try:
                # now convert the entry to a database object
                cls.objects.update_or_create(
                    id=entry["activity_id"],
                    defaults=dict(
                        chembl_document_id=entry["doc_id"],
                        chembl_compound_id=entry["molregno"],
                        value_relation=entry["standard_relation"],
                        value=entry["standard_value"],
                        value_units=entry["standard_units"],
                        data_validity_check=bool(entry["standard_flag"]),
                        value_type=entry["standard_type"],
                        activity_comment=entry["activity_comment"],
                        data_validity_comment=entry["data_validity_comment"],
                        is_potential_duplicate=bool(entry["potential_duplicate"]),
                        value_range_max=entry["standard_upper_value"],
                        value_text=entry["standard_text_value"],
                        mode_of_action_type=entry["action_type"],
                        description=entry["assay_description"],
                        target_organism=entry["assay_organism"],
                        confidence_score=entry["confidence_score"],
                        assay_type=entry["assay_type_description"],
                        assay_type_standard=entry["bao_type"],
                    ),
                )
            except:
                failed_rows.append(entry)

        logging.info("Done!")
        return failed_rows
