# -*- coding: utf-8 -*-

import random
import string

from django.contrib.auth.models import User

from simmate.database.core import DatabaseTable, table_column


class Substance(DatabaseTable):
    """
    A unique, registered chemical identity, such as an element, molecule,
    molecular salt, or material.

    Each substance gets a human-readable ID (e.g. `BCD-012-3456`) and can be
    linked to its molecular or crystal structure, to entries in third-party
    datasets (e.g. PubChem or the Materials Project), and to related substances
    (e.g. stereoisomers or phases via `parent`). Physical samples of a
    substance are tracked as `Batch` entries, and substances can also be
    combined into a `Mixture`.
    """

    class Meta:
        db_table = "inventory_management__substances"

    # -------------------------------------------------------------------------

    id = table_column.CharField(max_length=12, primary_key=True)
    """
    The unique, human-readable ID of the substance (e.g. `BCD-012-3456`).

    IDs follow the format of a phone number, but with letters in the first group:
        {3 letters}-{3 numbers}-{4 numbers}

    Letters are uppercase consonants excluding Y (20 options), and numbers
    are 0-9.
    
    **Why this format?**

    - Integer IDs (1, 2, 3, ...) are hard to read once large (e.g. 52614354),
      and they are continuous, so a single typo usually points to a different
      but valid entry.
    - UUIDs solve the typo problem but are far less readable.
    - The phone number layout (000-000-0000) is familiar and easy to read.
      Replacing the first group with letters increases the number of possible
      IDs and makes accidental matches from typos rare.
    - Letters also make the ID distinct from other formats (such as real phone
      numbers), giving it a recognizable look: "that's a Simmate substance ID".
    - Vowels and Y are excluded so that IDs never spell real words, which
      avoids accidental profanity or otherwise offensive/sensitive terms.

    **ID Levels**

    The base format allows for (20**3) * (10**7) = 80 billion unique IDs. To
    support massive enumerated catalogs (e.g. >100 billion compounds), IDs are
    assigned at one of three "levels", where each level converts the next
    number group into letters:

        Level 1: LLL-000-0000  (80 billion IDs)
        Level 2: LLL-LLL-0000  (640 billion IDs)
        Level 3: LLL-LLL-LLLL  (10.24 trillion IDs)
    
    Level 1 is reserved for substances that are certified, well known, 
    and/or have been experimentally synthesized, while levels 2 and 3
    are used for massive enumerated/virtual catalogs.

    Further levels (e.g. mixing letters and numbers within a group, or
    case-sensitive letters) are possible but not implemented, as they would
    overlap with the formats above and be harder to read and retype.
    """

    check_digit = table_column.CharField(max_length=1, blank=True, null=True)
    """
    A single-letter checksum of the `id` (e.g. `K` for `BCD-012-3456`).

    This is kept separate from the ID so that the ID stays short and readable,
    but it can be shown alongside the ID (e.g. `BCD-012-3456 / K`) and used to
    confirm that a typed ID is valid before searching the database. This
    matters because the table can potentially contain billions of entries, and
    a typo otherwise requires a full lookup before we can say "this ID does
    not exist".

    The check digit is calculated with the Luhn mod N algorithm (N=20) and is
    always one of the consonants used in IDs. It works for all ID levels.
    See `calculate_check_digit` for details.
    """

    # the difference can get blurry here but I have this primarily to indicate
    # the best defaults for rendering the compound (e.g. 2D flat vs 3D crystal)
    # and writing its chemical formula (reduced vs full) in the overview. It
    # can also help with workup via toolkit
    substance_type_options = [
        "element",
        "molecule",  # aka compound
        "molecular_salt",  # aka charged compound + counterion
        "material",  # aka alloy, crystal, etc
        "other",
        # out of scope:
        # "polymer",
        # "protein/biopolymer",
        # "meta_material",
    ]
    substance_type = table_column.CharField(
        max_length=15,
        blank=True,
        null=True,
    )
    """
    The general category of the substance. Must be one of
    `substance_type_options`.
    """

    description = table_column.TextField(blank=True, null=True)
    """
    Any extra details about the substance.
    """

    # -------------------------------------------------------------------------

    # SPECIAL CASES - most entries should have these all set to False

    is_theoretical = table_column.BooleanField(blank=True, null=True, default=False)
    """
    Whether the substance has been experimentally synthesized before or if it is a
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

    This allows private entities to register/reserve a unique ID, so that a
    private instance can stay in sync with the public registry without
    revealing the substance. Then, if the substance is later made public,
    there are no conflicting records of what the ID is (and the ID is
    guaranteed to not already be taken).
    """

    is_unknown = table_column.BooleanField(blank=True, null=True, default=False)
    """
    This exists for when you have a batch that contains a substance unknown by 
    the submitter and there is no reasonable guess as to what the substance 
    is. You should also have reason to believe the unknown is a single novel
    compound.
    
    Once the compound is known...
    - if it is in fact a new substance, associated batches retains this substance 
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
    The user that submitted the registration of this substance, effectively being
    the first to reserve the unique ID.
    
    In the open collective, Simmate makes registration cost $1 per substance - 
    but keep in mind that registration is only ever needed for novel materials 
    because any already experimentally known + theoretically stable substances 
    are automatically added by our team.
    
    We put the $1 fee in place in order to deter users from abusing the public
    forms with too many submissions. Otherwise, users would not be able 
    to register new substances without manual intervention/review by our team
    (which would slow down teams & make them wait to register something new).
    
    In cases where waiting is okay, you can also send our team a request to get
    your substance added for free (excluding `is_private=True` submissions).

    If the substance also needs to be delisted, this field can be used to refund
    the user.
    """

    projects = table_column.ManyToManyField(
        "project_management.Project",
        blank=True,
        related_name="substances",
        db_table="inventory_management__substance_projects",
    )
    """
    The projects that this substance is associated with.
    """

    # -------------------------------------------------------------------------

    common_name = table_column.CharField(max_length=255, blank=True, null=True)
    """
    The name that the substance is most commonly referred to by.
    """

    iupac_name = table_column.TextField(blank=True, null=True)
    """
    The systematic IUPAC name of the substance.
    """

    synonyms = table_column.JSONField(blank=True, null=True, default=list)
    """
    A list of other names that the substance is known by.
    """

    # -------------------------------------------------------------------------

    molecule = table_column.ForeignKey(
        "Molecule",
        on_delete=table_column.SET_NULL,
        related_name="substances",
        blank=True,
        null=True,
    )
    """
    The molecular structure associated with this substance. 
    
    Multiple substances can share the same molecule (e.g., different crystal 
    phases of the same molecule), but each substance can have only one molecule.
    """

    structure = table_column.ForeignKey(
        "Structure",
        on_delete=table_column.SET_NULL,
        related_name="substances",
        blank=True,
        null=True,
    )
    """
    The crystal structure associated with this substance.
    """

    # -------------------------------------------------------------------------

    is_primary = table_column.BooleanField(
        default=False,
        blank=True,
        null=True,
    )
    """
    Whether the substance is the primary reference for a given composition or 
    compound. This is typically the top-level "parent" and/or the most commonly 
    occurring (and stable) phase.
    """

    parent = table_column.ForeignKey(
        "Substance",
        on_delete=table_column.SET_NULL,
        related_name="children",
        blank=True,
        null=True,
    )
    """
    The parent substance that this entry is derived from. For example, a 
    specific stereoisomer or metastable phase would point to the more general 
    "flat" or "stable" substance.
    """

    is_metastable = table_column.BooleanField(
        default=False,
        blank=True,
        null=True,
    )
    """
    Whether the substance is a metastable phase.
    """

    has_stereochem = table_column.BooleanField(
        default=False,
        blank=True,
        null=True,
    )
    """
    Whether the substance has stereochemistry.
    """

    stereomchem_type_options = [
        "constitutional",  # for the flat/parent structure
        # configurational
        "enantiomer",
        "diastereomer",
        "geometric_isomer",
        "meso_compound",
        "epimer",
        "anomer",
        # conformational
        "rotamer",
        "atropisomer",
        "invertomer",
    ]
    stereochem_type = table_column.JSONField(
        blank=True,
        null=True,
    )
    """
    The specific stereochemical classification(s) of the substance. Values
    should be from `stereomchem_type_options`.

    Stereoisomer Classification (Same connectivity, different 3D arrangement)
        ├── Configurational (Bonds must break to interconvert)
        │   ├── Enantiomers (Non-superimposable mirror images)
        │   └── Diastereomers (Non-mirror images)
        │       ├── Geometric Isomers (cyclic Cis/Trans or double bond E/Z)
        │       ├── Meso Compounds (Achiral due to internal symmetry)
        │       └── Epimers/Anomers (Differ at specific centers)
        │
        └── Conformational (Rotation/flexing without breaking bonds)
            ├── Rotamers (e.g., Staggered vs. Eclipsed)
            ├── Atropisomers (Restricted rotation due to steric bulk)
            ├── Ring Conformers (Chair, Boat, Envelope)
            └── Invertomers (Rapid atomic inversion, e.g., Amines)
    
    Because this table also stores flat versions of stereoisomers, we include
    `constitutional` as an extra type to label these ones that contain
    unspecified stereochemistry
    """
    # is_prochiral # Prochiral (Can become chiral in a single step)

    stereochem_key = table_column.CharField(
        max_length=25,
        blank=True,
        null=True,
    )
    """
    A short key that distinguishes stereoisomers that share the same flat
    structure (e.g. to be used alongside an InChI key).
    """
    # TODO: key to add on to the inchi key to distinguish and query different
    # isomers -- like cis/trans labels, but also need keys for other types
    # and also combos. Need to think on this more... could even be integer ranking

    # -------------------------------------------------------------------------

    # Molecular datasets
    # Each of these links to the matching entry in a third-party dataset, if
    # one exists. Note `pubchem` stores the PubChem CID rather than a link.

    bcpc = table_column.ForeignKey(
        "bcpc.BcpcIsoPesticide",
        on_delete=table_column.SET_NULL,
        related_name="substances",
        blank=True,
        null=True,
    )

    cas_registry = table_column.ForeignKey(
        "cas_registry.CasRegistryMolecule",
        on_delete=table_column.SET_NULL,
        related_name="substances",
        blank=True,
        null=True,
    )

    chembl = table_column.ForeignKey(
        "chembl.ChemblMolecule",
        on_delete=table_column.SET_NULL,
        related_name="substances",
        blank=True,
        null=True,
    )

    chemspace = table_column.ForeignKey(
        "chemspace.ChemSpaceFreedomSpaceMolecule",
        on_delete=table_column.SET_NULL,
        related_name="substances",
        blank=True,
        null=True,
    )

    emolecules = table_column.ForeignKey(
        "emolecules.EmoleculesMolecule",
        on_delete=table_column.SET_NULL,
        related_name="substances",
        blank=True,
        null=True,
    )

    enamine = table_column.ForeignKey(
        "enamine.EnamineRealMolecule",
        on_delete=table_column.SET_NULL,
        related_name="substances",
        blank=True,
        null=True,
    )

    pdb = table_column.ForeignKey(
        "pdb.PdbLigand",
        on_delete=table_column.SET_NULL,
        related_name="substances",
        blank=True,
        null=True,
    )

    ppdb = table_column.ForeignKey(
        "ppdb.PpdbMolecule",
        on_delete=table_column.SET_NULL,
        related_name="substances",
        blank=True,
        null=True,
    )

    pubchem = table_column.CharField(
        max_length=20,
        blank=True,
        null=True,
    )
    """
    The PubChem compound ID (CID) of the substance.
    """

    # -------------------------------------------------------------------------

    # Crystalline datasets
    # Each of these links to the matching entry in a third-party dataset, if
    # one exists.

    aflow = table_column.ForeignKey(
        "aflow.AflowStructure",
        on_delete=table_column.SET_NULL,
        related_name="substances",
        blank=True,
        null=True,
    )

    cod = table_column.ForeignKey(
        "cod.CodStructure",
        on_delete=table_column.SET_NULL,
        related_name="substances",
        blank=True,
        null=True,
    )

    jarvis = table_column.ForeignKey(
        "jarvis.JarvisStructure",
        on_delete=table_column.SET_NULL,
        related_name="substances",
        blank=True,
        null=True,
    )

    materials_project = table_column.ForeignKey(
        "materials_project.MatprojStructure",
        on_delete=table_column.SET_NULL,
        related_name="substances",
        blank=True,
        null=True,
    )

    oqmd = table_column.ForeignKey(
        "oqmd.OqmdStructure",
        on_delete=table_column.SET_NULL,
        related_name="substances",
        blank=True,
        null=True,
    )

    # -------------------------------------------------------------------------

    extra_metadata = table_column.JSONField(blank=True, null=True)
    """
    Any additional data about the substance that does not fit in the columns
    above.
    """

    # -------------------------------------------------------------------------

    # Define consonants list by removing vowels and Y from the uppercase alphabet
    # We exclude these to prevent accidental formation of real words, which in
    # some cases can have negative consequences (profanity, politics, violence, etc)
    _LETTERS = "BCDFGHJKLMNPQRSTVWXZ"  # instead of string.ascii_uppercase

    @classmethod
    def generate_id(cls, level: int = 1) -> str:
        """
        Generates a readable ID at the given level (1-3). Level 1 is the format:
            {3 Letters}-{3 Numbers}-{4 Numbers}

        Each higher level swaps the next group of numbers for letters. See
        the docstring of the `id` column for all formats.

        Letters are not allowed to be vowels or the letter Y. Numbers are 0-9.
        """
        assert 1 <= level <= 3, f"Unknown ID level: {level}"
        return "-".join(
            "".join(
                random.choices(cls._LETTERS if i < level else string.digits, k=size)
            )
            for i, size in enumerate((3, 3, 4))
        )

    @classmethod
    def get_id_level(cls, substance_id: str) -> int | None:
        """
        Returns the level of the given ID, or None if it is not a valid format.
        """
        groups = substance_id.split("-")
        if [len(g) for g in groups] != [3, 3, 4]:
            return None
        for level in (1, 2, 3):
            letters = "".join(groups[:level])
            numbers = "".join(groups[level:])
            if all(c in cls._LETTERS for c in letters) and all(
                c in string.digits for c in numbers
            ):
                return level
        return None

    @classmethod
    def generate_unique_id(cls, level: int = 1) -> str:
        """
        Generates an ID at the given level that is not already in use.
        """
        return cls.generate_unique_ids(count=1, level=level)[0]

    @classmethod
    def generate_unique_ids(cls, count: int, level: int = 1) -> list[str]:
        """
        Generates IDs at the given level that are not already in use and are
        unique amongst themselves (e.g. for bulk importing a catalog).
        """
        new_ids = set()
        while len(new_ids) < count:
            nremaining = count - len(new_ids)
            candidates = {cls.generate_id(level) for _ in range(min(nremaining, 2_000))}
            candidates -= new_ids
            taken = cls.objects.filter(id__in=candidates).values_list("id", flat=True)
            new_ids.update(candidates.difference(taken))
        return list(new_ids)

    # -------------------------------------------------------------------------

    # The check digit uses the Luhn mod N algorithm with N=20 so that it is
    # always one of our consonants. Each character is mapped to a value in
    # 0-19: letters use their index in _LETTERS and digits use their own value.
    # Because the ID format fixes which positions are letters vs digits (at
    # every level), each position's characters map to unique values, so all
    # single-character typos and nearly all adjacent swaps are detected. Swaps
    # between a letter and a digit change the format and are caught by
    # `get_id_level` instead.

    @classmethod
    def _id_char_value(cls, char: str) -> int:
        """
        Maps an ID character to its value (0-19) for the check digit calculation.
        """
        return int(char) if char.isdigit() else cls._LETTERS.index(char)

    @classmethod
    def calculate_check_digit(cls, substance_id: str) -> str:
        """
        Calculates the single-letter check digit for an ID of any level.
        """
        substance_id = substance_id.upper()
        if not cls.get_id_level(substance_id):
            raise ValueError(f"Invalid substance ID format: {substance_id}")

        base_n = len(cls._LETTERS)  # 20
        total = 0
        for i, char in enumerate(reversed(substance_id.replace("-", ""))):
            value = cls._id_char_value(char)
            # double every other value, starting with the rightmost
            if i % 2 == 0:
                value *= 2
                # sum the "digits" in base N to keep it within 0 to N-1
                value = (value // base_n) + (value % base_n)
            total += value
        return cls._LETTERS[(base_n - (total % base_n)) % base_n]

    @classmethod
    def validate_id(cls, substance_id: str, check_digit: str | None = None) -> bool:
        """
        Checks that the ID has a valid format and, if a check digit is given,
        that it matches the ID. This does not check the database.
        """
        substance_id = substance_id.upper()
        if not cls.get_id_level(substance_id):
            return False
        if check_digit is None:
            return True
        return check_digit.upper() == cls.calculate_check_digit(substance_id)

    # -------------------------------------------------------------------------
