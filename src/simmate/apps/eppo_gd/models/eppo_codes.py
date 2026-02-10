# -*- coding: utf-8 -*-

from simmate.database.base_data_types import DatabaseTable, table_column

from ..client import EppoWebScrapper

# for testing
_MAJOR_CROP_CODES = [
    "ZEAMA",  # Maize / Corn
    "TRZAX",  # Common wheat
    "SOLTU",  # Potato
    "ORYSA",  # Rice
    "GLYMA",  # Soybean
    "GOSHI",  # Cotton
]


class EppoCode(DatabaseTable):
    """
    EPPO Codes are labels to provide all pest-specific information that has been
    produced or collected by the European and Mediterranean Plant Protection
    Organization (EPPO)

    This table includes codes and metadata pulled lazily from the official
    [EPPO website](https://gd.eppo.int/).

    Note that some organizations use internal codes as well,
    so this table can include additional codes with a custom "eppo_source".
    """

    class Meta:
        db_table = "eppo_gd__eppo_codes"

    html_display_name = "EPPO Global Database"
    html_description_short = (
        "EPPO codes and metadata for >95k species of interest to agriculture. "
        "Codes are loaded 'lazily' from EPPO GD, and so this is not a complete list "
        "of crops, pests, and pathogens."
    )
    is_redistribution_allowed = True

    external_website = "https://gd.eppo.int/"

    html_entries_template = "eppo_gd/eppo_codes/table.html"
    # html_entry_template = "eppo_gd/eppo_codes/view.html"

    # -------------------------------------------------------------------------

    # disable cols
    source = None

    id = table_column.CharField(max_length=25, primary_key=True)
    """
    The ID is the actual EPPO code. Typically these are no more than 6 characters
    but some internal codes may be longer.
    """

    eppo_source = table_column.CharField(max_length=25, blank=True, null=True)
    """
    Where the EPPO code originated from. Typically this is "eppo_global_db",
    but can sometime be an separate source such as "simmate_user".
    """

    preferred_name = table_column.TextField(blank=True, null=True)
    """
    The preferred name for this entry. Typically this is the preferred
    scientific name and matches its species name. However, this field can
    be overwritten to a preferred common name if desired.
    """

    common_names = table_column.JSONField(blank=True, null=True)
    """
    A list of common names that are used for this species (e.g. "stinkbug")
    """

    other_scientific_names = table_column.JSONField(blank=True, null=True)
    """
    A list of alternative scientific names that are used for this species
    """

    # --- BEGIN TAXONOMY FIELDS ---

    kingdom = table_column.TextField(blank=True, null=True)
    """
    The "kingdom" for this entry's taxonomy tree
    """

    phylum = table_column.TextField(blank=True, null=True)
    """
    The "phylum" for this entry's taxonomy tree
    """

    subphylum = table_column.TextField(blank=True, null=True)
    """
    The "subphylum" for this entry's taxonomy tree
    """

    # BUG: I can't set this name to just class
    #   https://stackoverflow.com/questions/73838954
    class_name = table_column.TextField(blank=True, null=True, db_column="class")
    """
    The "class" for this entry's taxonomy tree
    """

    subclass = table_column.TextField(blank=True, null=True)
    """
    The "subclass" for this entry's taxonomy tree
    """

    category = table_column.TextField(blank=True, null=True)
    """
    The "category" for this entry's taxonomy tree
    """

    order = table_column.TextField(blank=True, null=True)
    """
    The "order" for this entry's taxonomy tree
    """

    suborder = table_column.TextField(blank=True, null=True)
    """
    The "suborder" for this entry's taxonomy tree
    """

    family = table_column.TextField(blank=True, null=True)
    """
    The "family" for this entry's taxonomy tree
    """

    subfamily = table_column.TextField(blank=True, null=True)
    """
    The "subfamily" for this entry's taxonomy tree
    """

    genus = table_column.TextField(blank=True, null=True)
    """
    The "genus" for this entry's taxonomy tree
    """

    species = table_column.TextField(blank=True, null=True)
    """
    The "species" for this entry's taxonomy tree
    """

    @property
    def external_link(self) -> str:
        """
        URL to this molecule in the EPPO website.
        """
        # ex: https://gd.eppo.int/taxon/LAPHEG
        return f"https://gd.eppo.int/taxon/{self.id}"

    # -------------------------------------------------------------------------

    @classmethod
    def load_source_data(
        cls,
        eppo_codes: list[str] = None,
        update_only: bool = False,
        **kwargs,
    ):
        """
        Loads all EPPO codes directly for the EPPO website into the local
        Simmate database.
        """

        if not eppo_codes:
            eppo_codes = _MAJOR_CROP_CODES.copy()

        if update_only and cls.objects.exists():
            skip_codes = list(cls.objects.values_list("id", flat=True).all())
        else:
            skip_codes = []

        eppo_codes = [c for c in eppo_codes if c not in skip_codes]
        all_data = EppoWebScrapper.get_all_eppo_code_data(
            eppo_codes=eppo_codes,
            **kwargs,
        )

        for entry in all_data:

            entry["id"] = entry.pop("eppo_code")

            # BUG-FIX: "class" key must be "class_name" to work
            if "class" in entry.keys():
                entry["class_name"] = entry.pop("class")

            # BUG-FIX: replace encoding issues
            if "other_scientific_names" in entry.keys():
                entry["other_scientific_names"] = [
                    n.replace("è", "e").replace("é", "e")
                    for n in entry.pop("other_scientific_names")
                ]
            if "common_names" in entry.keys():
                entry["common_names"] = [
                    n.replace("è", "e").replace("é", "e")
                    for n in entry.pop("common_names")
                ]
            if "subfamily" in entry.keys():
                entry["subfamily"] = entry.pop("subfamily").replace("ö", "o")

            # remove some unwanted fields
            entry.pop("name_authority", None)

            new_db_obj = cls(**entry)
            new_db_obj.save()  # consider get_or_create to update things
