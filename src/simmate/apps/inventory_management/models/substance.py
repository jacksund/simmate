# -*- coding: utf-8 -*-

import random
import string

from django.contrib.auth.models import User

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
        - vowels and Y are excluded from letters to prevent accidental 
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

    # SPECIAL CASES - most entries should have these all set to False

    is_theoretical = table_column.BooleanField(blank=True, null=True, default=False)
    """
    Whether the substance has been experimentally synthesized before or if is a
    purely theoretical compound.

    We allow theoretical compounds to be registered for cases such as predicted
    thermodynamic stability as well as targeted synthesis tracking. Private
    servers may also use this more generally such as for tracking a full 
    list of candidate compounds.
    """

    is_delisted = table_column.BooleanField(blank=True, null=True, default=False)
    """
    Whether the substance has been removed from the catalog.
    
    When an entry needs to be removed, we can wipe the data, keep the ID in
    place (to avoid future conflicts/confusion), and set the entry as `is_delisted=True`.
    
    This can happen with accidental duplicates, typos, and general cleanup.
    """

    is_private = table_column.BooleanField(blank=True, null=True, default=False)
    """
    Whether this is a private substance, where the substance is intentionally
    kept secret. Do not confuse with `is_unknown` where the substance
    is truly unknown even by the submitter.
    
    so that private entities can register/reserve a unique ID. This
    makes it so that you have a private instance in sync with the public
    registry without revealing your substance. Therefore when the substance
    is made public + registered to this table, there are not conflicting 
    records of what the ID is (+ ensures their ID isn't already taken)
    """

    is_unknown = table_column.BooleanField(blank=True, null=True, default=False)
    """
    This exists for when you have a batch that contains a substance unknown by 
    the submitter and there is no reasonable guess as to what the substance 
    is. You should also have reason to believe the unknown is a single novel
    compound.
    
    Once the compound is known...
    - if it is in fact a new substace, associated batches retains this substance 
      ID and the entry is updated with the structure
    - if the substance ends up being something already registered, this ID 
      becomes delisted and all associated batches have their link switched
      to the correct ID.
    
    In 99.9% of cases, you are better off assigning an educated guess to a batch,
    such as saying "I think I synthesized ___ but will switch the substance ID 
    if I characterize it and find it to be something else". If it ends up
    being an unwanted unknown (e.g., a failed synthesis), keep the targeted
    substance ID and update your batch comments + purity metadata to indicate
    this -- there is no need for a unique substance ID for each failed reaction.
    
    The most common case where you need to register an unknown substance is
    when you have assay data for it before any guess/characterization can be
    done.
    """

    # -------------------------------------------------------------------------

    registered_by = table_column.ForeignKey(
        User,
        on_delete=table_column.PROTECT,
        related_name="registered_substances",
        blank=True,
        null=True,
    )
    """
    The user that submitted the regstration of this substance, effectively being
    the first to reserve the unique ID.
    
    In the open collective, Simmate makes registration cost $1 per substance - 
    but keep in mind that registration is only ever needed for novel materials 
    because any already experimentally known + theoretically stable substances 
    are automatically added by our team.
    
    We put the $1 fee in place in order to deter users from abusing the public
    forms with too many submissions. Otherwise, users would not be able 
    to register new substances without manual intervetion/review by our team
    (which would slow down teams & make them wait to register something new).
    
    In cases where waiting is okay, you can also send our team a request to get
    your substance added for free (excluding `is_private=True` submissions).

    If the substance also needs to be delisted, this field can be used to refund
    the user.
    """

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

    extra_metadata = table_column.JSONField(blank=True, null=True)

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
