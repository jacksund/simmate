# -*- coding: utf-8 -*-

import logging
from pathlib import Path

import pandas
from rich.progress import track

from simmate.database.base_data_types import DatabaseTable, table_column
from simmate.utilities import chunk_list, get_hash_key

from .molecules import EmoleculesMolecule


class EmoleculesSupplierOffer(DatabaseTable):
    """
    Vendors and their prices for 'building-block' molecules from the
    [eMolecules](https://www.emolecules.com/) database.
    """

    # disable cols
    source = None

    html_display_name = "eMolecules Building Blocks Offers"
    html_description_short = "A vendor catalog of chemical 'building-blocks'"

    external_website = "https://www.emolecules.com/"
    source_doi = "https://www.emolecules.com/data-downloads"

    id = table_column.CharField(
        primary_key=True,
        max_length=32,
    )
    """
    The ID here is a MD5 hash-key of...
        - when `supplier_name` is 'eMolecules (custom)':
            - `compound_id`
            - `tier_number`
            - `price_per_unit`
            - `grams_per_unit`
        - when `supplier_name` is anything else
            - `compound_id`
            - `sku`
    """

    compound = table_column.ForeignKey(
        to=EmoleculesMolecule,
        related_name="vendor_offers",
        on_delete=table_column.PROTECT,
    )
    """
    The ID of the compound in the eMolecules compound table. Within eMolecules,
    this is also referred to as the "version_id"
    """

    # supplier_id = table_column.IntegerField(blank=True, null=True)
    # """
    # The ID of the supplier within the eMolecules database
    # """  # --> dont really need this until suppliers are put in separate table

    supplier_name = table_column.TextField(blank=True, null=True)
    """
    The name of the supplier that offers this chemical.
    """

    supplier_compound_id = table_column.TextField(blank=True, null=True)
    """
    The ID of this product/chemical within the supplier's database
    """

    grams_per_unit = table_column.FloatField(blank=True, null=True)
    """
    The amount of material that represents 1 unit
    """

    price_per_unit = table_column.FloatField(blank=True, null=True)
    """
    The price for 1 unit of this material in United States Dolars ($).
    """

    # currency = table_column.TextField(blank=True, null=True)
    # """
    # The currency that `price` is listed in. Most of these give `USD` for
    # the United States Dollar
    # """
    # the entire column they give is in USD... So this isn't needed

    price_per_gram = table_column.FloatField(blank=True, null=True)
    """
    Gives the $/g offer. This column is calculated using the `grams`, `price`,
    and `currency` columns if all 3 are available.
    """

    tier_number = table_column.IntegerField(blank=True, null=True)
    """
    The Tier number assigned to this product by eMolecules.
    """
    # TODO: I think tier refers to lead time... Need to look into this.

    sku = table_column.IntegerField(blank=True, null=True)
    """
    This ID uses eMolecule's SKU (Stock Keeping Unit) ID. 
    
    Typically, this would be the primary key for this table BUT there are two
    issues...
        1. eMolecules doesn't maintain this super well, so there are duplicates.
           Last check, only 0.27% of entries have duplicates and within the
           list of duplicates, 86% of them match the full row. The remaining
           entries (typically) only differ in `version_id`
        2. Some companies pay for a custom stockpile. These are stored by eMol
           and the tsv they provide does *not* include any sku.
    """

    # -------------------------------------------------------------------------

    # NOTE: The `_load_data` calls for this class are actually within the
    # `Emolecules._load_data` method. This is because that's where the necessary
    # downloads are handled and it was easier to code out.

    @classmethod
    def _load_building_blocks_metadata(
        cls,
        metadata_file: str | Path = "metadata.tsv",
        update_only: bool = False,
    ):

        logging.info("Loading metadata...")
        vendor_offers = pandas.read_csv(metadata_file, sep="\t")
        all_ids = set(Emolecules.objects.values_list("id", flat=True).all())

        # To make things faster so that we can bulk upload, we want to remove
        # all "offers" in the dataframe that don't have a matching emol id in
        # our database (these cause the full bulk_create to fail). We can also
        # limit our ID list to version_max if this is a continuation.
        vendor_offers = vendor_offers[vendor_offers.version_id.isin(all_ids)]

        # add hash key column, which is the pk for this table
        vendor_offers["hash_key"] = [
            get_hash_key(f"{row.version_id} {row.sku}")
            for i, row in vendor_offers.iterrows()
        ]

        if update_only:
            all_offer_ids = set(vendor_offers.hash_key.to_list())
            simmate_offer_ids = set(cls.objects.values_list("id", flat=True).all())
            offer_ids_to_update = all_offer_ids - simmate_offer_ids
            vendor_offers = vendor_offers[
                vendor_offers.hash_key.isin(offer_ids_to_update)
            ]

        chunk_size = 25_000
        nchunk = 0
        nchunks_total = (len(vendor_offers) // chunk_size) + 1
        failed = []
        for emol_chunk in chunk_list(vendor_offers, chunk_size):

            logging.info(f"CHUNK # {nchunk} of {nchunks_total}")
            nchunk += 1

            logging.info("Generating database objects...")
            db_objs = []
            for i, row in track(emol_chunk.iterrows(), total=len(emol_chunk)):
                try:
                    new_obj = cls(
                        id=row.hash_key,
                        compound_id=row.version_id,
                        supplier_name=row.supplier_name,
                        grams_per_unit=row.grams,
                        price_per_unit=row.price,
                        price_per_gram=(
                            row.price / row.grams if row.grams and row.price else None
                        ),
                        tier_number=row.tier_num,
                        sku=row.sku,
                    )
                    db_objs.append(new_obj)
                except:
                    failed.append(row.to_dict())

            logging.info("Saving to Simmate database...")
            cls.objects.bulk_create(
                db_objs,
                batch_size=1000,
                ignore_conflicts=True,
                # BUG: is it possible for an entry to change...?
                # update_conflicts=True,
                # unique_fields=["id"],
                # update_fields=[...],
            )

        return failed

    @classmethod
    def _load_custom_pricestable(
        cls,
        custom_file: str = "example_pricestable.tsv",
        update_only: bool = False,
    ):
        # !!! While this method is close to _load_metadata, there are subtle
        # differences. Read closely.

        logging.info("Loading metadata...")
        # BUG: this is a tsv file, but emol uses a mix of tabs AND commas...
        # So I need to do some funky patching here.
        custom_offers = pandas.read_csv(custom_file, sep="\t|,", engine="python")
        custom_offers.rename(columns={" tier_num": "tier_num"}, inplace=True)

        all_ids = set(Emolecules.objects.values_list("id", flat=True).all())

        # To make things faster so that we can bulk upload, we want to remove
        # all "offers" in the dataframe that don't have a matching emol id in
        # our database (these cause the full bulk_create to fail). We can also
        # limit our ID list to version_max if this is a continuation.
        custom_offers = custom_offers[custom_offers.version_id.isin(all_ids)]

        # parse the packsize column into a grams column to align with bb
        # ALL entries have 3 mg give... so we just take a shortcut here.
        assert custom_offers.packsize.nunique() == 1
        # assert custom_offers.packsize[0] == "3 mg"
        custom_offers["grams"] = 0.003

        custom_offers["hash_key"] = [
            get_hash_key(
                f"{row.version_id} {row.grams} {row.retail_price} {row.tier_num}"
            )
            for i, row in custom_offers.iterrows()
        ]

        if update_only:
            all_offer_ids = set(custom_offers.hash_key.to_list())
            simmate_offer_ids = set(
                cls.objects.filter(supplier_name="eMolecules (custom)")
                .values_list("id", flat=True)
                .all()
            )
            offer_ids_to_update = all_offer_ids - simmate_offer_ids
            custom_offers = custom_offers[
                custom_offers.hash_key.isin(offer_ids_to_update)
            ]

        chunk_size = 25_000
        nchunk = 0
        nchunks_total = (len(custom_offers) // chunk_size) + 1
        failed = []
        for emol_chunk in chunk_list(custom_offers, chunk_size):

            logging.info(f"CHUNK # {nchunk} of {nchunks_total}")
            nchunk += 1

            logging.info("Generating database objects...")
            db_objs = []
            for i, row in track(emol_chunk.iterrows(), total=len(emol_chunk)):
                try:
                    new_obj = cls(
                        id=row.hash_key,
                        compound_id=row.version_id,
                        supplier_name="eMolecules (custom)",
                        grams_per_unit=row.grams,
                        price_per_unit=row.retail_price,
                        price_per_gram=(
                            row.retail_price / row.grams
                            if row.grams and row.retail_price
                            else None
                        ),
                        tier_number=row.tier_num,
                    )
                    db_objs.append(new_obj)
                except:
                    failed.append(row.to_dict())

            logging.info("Saving to Simmate database...")
            cls.objects.bulk_create(
                db_objs,
                batch_size=1000,
                ignore_conflicts=True,
                # BUG: is it possible for an entry to change...?
                # update_conflicts=True,
                # unique_fields=["id"],
                # update_fields=[...],
            )

        return failed
