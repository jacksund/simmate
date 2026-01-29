# -*- coding: utf-8 -*-

import random
import string

from simmate.database.base_data_types import DatabaseTable, table_column


class Substance(DatabaseTable):

    class Meta:
        db_table = "inventory_management__substances"

    html_display_name = "Chemical Substances"
    html_description_short = (
        "A substance is a specific element or compound with uniform composition+structure. "
        "As a general rule of thumb, if there is a CAS number (from ACS) or "
        "CID (from PubChem) assigned to it, then it is likely a chemical substance. "
        "In addition, this table includes both specified and unspecified "
        "stereochemical compounds, where flat structures and those with "
        "'and'/'or' notations are separate entries. Allotropes are also "
        "separate entries."
    )

    # -------------------------------------------------------------------------

    # disable cols
    source = None

    id = table_column.CharField(max_length=12, primary_key=True)
    """
    The unique ID assigned to each substance.
    
    IDs follow a format that make them more readable:
        {3 letters}-{3 numbers}-{4 numbers}
    
    Letters are not allowed to be vowels or the letter Y. And numbers are 0-9.

    This results in IDs such as...
        BCD-012-3456
    
    The fixed format means there are a finite number of unique IDs possible:
        (20**3)*(10**3)*(10**4) = 80 billion IDs
    
    As for how we arrived at this format:
        - an integer-based ID (1,2,3,4,...) has the downside of being difficult
          to read for large numbers (e.g. 52614354) and also continuous such
          that one typo likely references another different (but valid) entry
        - Relative to integer IDs, UUIDs fix the continuous issue but greatly 
          worsen the readability
        - The format we use is derrived from a familiar format of telephone
          numbers (000-000-0000), and to ensure more total possible IDs and to 
          make continuity rare, the first three entries were replaced with letters
        - the use of letters also helps to distinguish this format from others
          (such as real phone numbers). It gives the ID a "recognizable brand"
          where users can see it and go "that looks like a simmate substance id"
        - vowels and Y are excluded from letters these to prevent accidental 
          formation of real words, which in some cases can have 
          negative consequences (profanity, politics, voilence, etc)
    """

    substance_type_options = [
        "element",
        "molecule",  # aka compound
        "material",  # aka alloy, crystal, etc
        "other",
        # out of scope:
        # "polymer",
        # "protein/biopolymer",
    ]
    substance_type = table_column.CharField(
        max_length=15,
        blank=True,
        null=True,
    )

    description = table_column.TextField(blank=True, null=True)

    # -------------------------------------------------------------------------

    common_name = table_column.CharField(max_length=255, blank=True, null=True)

    iupac_name = table_column.TextField(blank=True, null=True)

    synonyms = table_column.JSONField(blank=True, null=True, default=list)

    # -------------------------------------------------------------------------

    # TODO:

    # composition
    # extra_metadata  (for "other" types)

    # molecule
    # has_stereochem
    #
    # Stereoisomer Classification
    #     ├── Configurational (Bonds must break to interconvert)
    #     │   ├── Enantiomers (Non-superimposable mirror images)
    #     │   └── Diastereomers (Non-mirror images)
    #     │       ├── Geometric Isomers (Cis/Trans or E/Z)
    #     │       ├── Meso Compounds (Achiral due to internal symmetry)
    #     │       └── Epimers/Anomers (Differ at specific centers)
    #     │
    #     └── Conformational (Rotation around single bonds)
    #         ├── Rotamers (e.g., Staggered vs. Eclipsed)
    #         ├── Atropisomers (Restricted rotation due to steric bulk)
    #         └── Invertomers (Rapid atomic inversion, e.g., Amines)

    # structure
    # is_metastable_phase
    # is_meta_material (if we decide to include these)

    # is_primary_substance (if it is main ref for a given composition or compound)
    # parent_substance (if has_stereochem and/or is_metastable_phase)

    # -------------------------------------------------------------------------

    bcpc = table_column.CharField(
        max_length=20,
        blank=True,
        null=True,
    )

    cas_number = table_column.CharField(
        max_length=20,
        blank=True,
        null=True,
    )

    chembl = table_column.CharField(
        max_length=20,
        blank=True,
        null=True,
    )

    chemspace = table_column.CharField(
        max_length=20,
        blank=True,
        null=True,
    )

    emolecules = table_column.CharField(
        max_length=20,
        blank=True,
        null=True,
    )

    enamine = table_column.TextField(blank=True, null=True)

    pdb = table_column.CharField(
        max_length=20,
        blank=True,
        null=True,
    )

    ppdb = table_column.CharField(
        max_length=20,
        blank=True,
        null=True,
    )

    pubchem_cid = table_column.CharField(
        max_length=20,
        blank=True,
        null=True,
    )

    # -------------------------------------------------------------------------

    aflow = table_column.CharField(
        max_length=20,
        blank=True,
        null=True,
    )

    cod = table_column.CharField(
        max_length=20,
        blank=True,
        null=True,
    )

    jarvis = table_column.CharField(
        max_length=20,
        blank=True,
        null=True,
    )

    materials_project = table_column.CharField(
        max_length=20,
        blank=True,
        null=True,
    )

    oqmd = table_column.CharField(
        max_length=20,
        blank=True,
        null=True,
    )

    # -------------------------------------------------------------------------

    @classmethod
    def generate_unique_id(cls, existing_ids: list[str] = None) -> str:

        if not existing_ids:
            existing_ids = cls.objects.values_list("id", flat=True).all()

        found_unique_id = False
        while not found_unique_id:
            new_id = cls.generate_id()
            if new_id not in existing_ids:
                found_unique_id = True

        return new_id

    @staticmethod
    def generate_id() -> str:
        """
        Generates a unique and readable id of the format...
            {3 letters}-{3 numbers}-{4 numbers}
        Letters are not allow to be vowels or the letter Y. Numbers are 0-9.
        """

        # Define consonants list by removing vowels and Y from the uppercase alphabet
        # We exclude these to prevent accidental formation of real words, which in
        # some cases can have negative consequences (profanity, politics, voilence, etc)
        LETTERS = "BCDFGHJKLMNPQRSTVWXZ"  # instead of string.ascii_uppercase

        letters_group = "".join(random.choices(LETTERS, k=3))
        num_group_1 = "".join(random.choices(string.digits, k=3))
        num_group_2 = "".join(random.choices(string.digits, k=4))

        return f"{letters_group}-{num_group_1}-{num_group_2}"
