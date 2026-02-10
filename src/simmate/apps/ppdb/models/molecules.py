# -*- coding: utf-8 -*-

import logging

from rich.progress import track

from simmate.apps.rdkit.models import Molecule
from simmate.database.base_data_types import table_column

from ..web_scraper import PpdbWebScraper


class PpdbMolecule(Molecule):
    """
    The PPDB is the 'Pesticide Properties DataBase' from a team at the
    University of Hertfordshire.

    There is both a base website and a mirror in the IUPAC website:
    - https://sitem.herts.ac.uk/aeru/ppdb/en/index.htm
    - https://sitem.herts.ac.uk/aeru/iupac/index.htm

    This table is pulled from the base website using the full index of compounds
    located here:
    - https://sitem.herts.ac.uk/aeru/ppdb/en/atoz.htm
    """

    class Meta:
        db_table = "ppdb__molecules"

    # disable cols
    source = None

    html_display_name = "PPDB"
    html_description_short = "The Pesticide Properties Database."

    html_entries_template = "ppdb/molecules/table.html"
    html_entry_template = "ppdb/molecules/view.html"

    external_website = "https://sitem.herts.ac.uk/aeru/ppdb/en/index.htm"
    source_doi = "https://sitem.herts.ac.uk/aeru/ppdb/en/atoz.htm"
    is_redistribution_allowed = False

    name = table_column.TextField(blank=True, null=True)
    """
    Chemical or common name of the compound
    """

    aliases = table_column.JSONField(blank=True, null=True)
    """
    alternative names and codes for the compound
    """

    summary = table_column.TextField(blank=True, null=True)
    """
    This is a short paragraph picking out the key parameters providing an overview
    of the pesticide substance and it chemical and (eco)toxicological properties.
    """

    description = table_column.TextField(blank=True, null=True)
    """
    General description of the major uses of the substance.
    """

    evironment_fate = table_column.TextField(blank=True, null=True)
    """
    A basic label assigned based on assay data. An absence of an alert does not 
    imply the substance has no implications for human health, biodiversity or 
    the environment but just that we do not have the data to form a judgement. 
    These hazard alerts do not take account of usage patterns or exposure, 
    thus do not represent risk.
    """

    ecotoxicity = table_column.TextField(blank=True, null=True)
    """
    A basic label assigned based on assay data. An absence of an alert does not 
    imply the substance has no implications for human health, biodiversity or 
    the environment but just that we do not have the data to form a judgement. 
    These hazard alerts do not take account of usage patterns or exposure, 
    thus do not represent risk.
    """

    human_health = table_column.TextField(blank=True, null=True)
    """
    A basic label assigned based on assay data. An absence of an alert does not 
    imply the substance has no implications for human health, biodiversity or 
    the environment but just that we do not have the data to form a judgement. 
    These hazard alerts do not take account of usage patterns or exposure, 
    thus do not represent risk.
    """

    pesticide_type = table_column.JSONField(blank=True, null=True)
    """
    The specific type of substance described according to the type of pest or
    disease they control e.g. Insecticide, Herbicide, Fungicide, Acaricide,
    Antiparasitic, Anthelmintic etc.
    """

    substance_groups = table_column.JSONField(blank=True, null=True)
    """
    Chemical classification group based on the chemical structure.
    """

    applications = table_column.JSONField(blank=True, null=True)
    """
    A non-exhaustive list of application situations.
    """

    pests_controlled = table_column.JSONField(blank=True, null=True)
    """
    A non-exhaustive list of pests that the substance controls.
    """

    mode_of_action = table_column.TextField(blank=True, null=True)
    """
    The mechanism by which the substance performs its main function.
    """

    known_resistances = table_column.TextField(blank=True, null=True)
    """
    Information on any known resistance issues for the substance.
    """

    efficacy_and_activity = table_column.TextField(blank=True, null=True)
    """
    Information on the efficacy and activity of the pesticide towards the pest or
    issue the substance is intended to control.
    """

    updated_at_original = table_column.DateTimeField(blank=True, null=True)
    """
    When the entry was last updated on the original PPDB website
    """

    key_dates = table_column.TextField(blank=True, null=True)
    """
    Various key dates in the substance’s history such as the date of discovery,
    patents, product launches, regulatory approval, withdrawal etc.
    """

    manufacturers_and_suppliers = table_column.JSONField(blank=True, null=True)
    """
    Examples of companies that have manufactured, supplied or used the
    substance in their products currently or historically.
    """

    product_names = table_column.JSONField(blank=True, null=True)
    """
    Non-exhaustive list of examples of products that include the substance. These
    products may be historical and no longer available.
    """

    formulation_details = table_column.TextField(blank=True, null=True)
    """
    This provides brief information on the main types of formulation and aspects
    relating to their application.
    """

    commercial_production_details = table_column.TextField(blank=True, null=True)
    """
    A short summary of the main production methods.
    """

    physical_state = table_column.TextField(blank=True, null=True)
    """
    Provides an indication of the physical state of the material – solid, liquid or gas
    and its general appearance. This normally applies to the active substance in its
    pure state unless stated otherwise.
    """

    availability_status = table_column.TextField(blank=True, null=True)
    """
    An indication of whether the substance is currently available or obsolete (if
    known).
    """

    hb_copr_regulatory_status = table_column.TextField(blank=True, null=True)
    """
    Status of the chemical in the US Honey Bee COPR regulatory review process
    for pesticide/biopesticide active substances.
    """

    ec_regulatory_status = table_column.TextField(blank=True, null=True)
    """
    Status of the chemical in the EU peer review process EC directive 1107/2009
    (repealing 91/414) of pesticide/biopesticide active substances
    """

    cas_number = table_column.TextField(blank=True, null=True)
    """
    Chemical Abstracts Service Registry Number - a unique identify for the
    chemical.
    """

    ec_number = table_column.TextField(blank=True, null=True)
    """
    The unique reference number for the chemical in the European Chemical
    Substances Information System (EINECS) or European List of Notified Chemicals
    (ELINCS).
    """

    cipac_number = table_column.TextField(blank=True, null=True)
    """
    The CIPAC code number system is a simple approach for an unambiguous
    coding of chemicals. CIPAC, FAO, WHO and the EU are the main users of this
    system.
    """

    us_epa_chemical_code = table_column.TextField(blank=True, null=True)
    """
    The U.S. Environmental Protection Agency (U.S. EPA) assigns a unique reference
    number to individual pesticide active ingredients to assist in their identification.
    This code is sometimes referred to as the Shaugnessy Number.
    """

    pubchem_cid = table_column.TextField(blank=True, null=True)
    """
    Identifier within the PubChem chemistry database of the National Institutes of
    Health (NIH).
    """

    clp_index_number = table_column.TextField(blank=True, null=True)
    """
    Official Index Number assigned to the chemical by the European Union under
    the Classification, Labelling, and Packaging (CLP) Regulation (EC) No 1272/2008.
    This number is used for regulatory identification of substances.
    """

    @property
    def external_link(self) -> str:
        """
        URL to this entry in the source website.
        """
        # ex: https://sitem.herts.ac.uk/aeru/ppdb/en/Reports/1234.htm
        return f"https://sitem.herts.ac.uk/aeru/ppdb/en/Reports/{self.id}.htm"

    # -------------------------------------------------------------------------

    @classmethod
    def load_source_data(cls, update_only: bool = False, **kwargs):
        """
        Loads all molecules directly for the BCPC website into the local
        Simmate database.
        """

        if update_only and cls.objects.exists():
            existing_ids = list(cls.objects.values_list("id", flat=True).all())
        else:
            existing_ids = []

        all_data = PpdbWebScraper.get_all_data(
            skip_ids=existing_ids,
            **kwargs,
        )

        logging.info("Saving to simmate database...")
        for entry_data in track(all_data):
            entry_id = entry_data.pop("id")
            try:
                cls.objects.update_or_create(
                    id=entry_id,
                    defaults=cls.from_toolkit(
                        as_dict=True,
                        **entry_data,
                    ),
                )
            except:
                logging.info(f"Failed to load entry {entry_id} into database")
                continue

        logging.info("Adding molecule fingerprints...")
        cls.populate_fingerprint_database()
