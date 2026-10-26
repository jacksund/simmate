import random
import string

from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.functional import classproperty

from simmate.config import settings
from simmate.database.core import DatabaseTable, table_column
from simmate.database.mixins import ThirdPartyData
from simmate.toolkit import Molecule as ToolkitMolecule

from .molecule import Molecule
from .structure import Structure
from .substance_id_change import SubstanceIdChange


class Substance(DatabaseTable):
    """
    A unique, registered chemical identity, such as an element, molecule,
    molecular salt, or material.

    Each substance gets a human-readable ID (e.g. `BCD-012-3456`) and can be
    linked to its molecular or crystal structure and to related substances
    (e.g. stereoisomers or phases via `parent`). This table is the central
    registry that other apps link to. For example, entries in third-party
    datasets (e.g. ChEMBL or the Materials Project) each point to their
    matching substance, available in reverse via `<app>_entries`. Physical samples of a
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
        "molecular_crystal",  # aka phase of a compound
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

    replaced_by = table_column.ForeignKey(
        "Substance",
        on_delete=table_column.SET_NULL,
        related_name="replaces",
        blank=True,
        null=True,
    )
    """
    For delisted substances, the substance that this ID now redirects to
    (e.g. after a merge or promotion).

    This always points to the *current* substance, so there is never a chain
    of redirects to follow (i.e. if A was merged into B and later B into C,
    then A points directly to C). See `resolve_id` and the
    `SubstanceIdChange` table for the full history.
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

    # Entries in third-party datasets (e.g. ChEMBL or the Materials Project)
    # link to this table via their own `substance` column, so that many entries
    # can point to the same substance. These are available in reverse via
    # `<app>_entries` (e.g. `substance.chembl_entries.all()`).

    # -------------------------------------------------------------------------

    extra_metadata = table_column.JSONField(blank=True, null=True)
    """
    Any additional data about the substance that does not fit in the columns
    above.
    """

    # -------------------------------------------------------------------------

    datastore_synced_at = table_column.DateTimeField(blank=True, null=True)
    """
    When this entry was last written to the `SubstanceDatastore`, which holds
    the full catalog (whereas this table only holds "hot" entries).

    The entry needs syncing if this is empty or older than `updated_at`. Note
    that `.update()` calls don't change `updated_at`, so they should set this
    to None instead. See `SubstanceDatastore.compact`.
    """

    # -------------------------------------------------------------------------

    @classproperty
    def linked_dataset_relations(cls) -> list:
        """
        The reverse relations from third-party dataset tables (e.g. ChEMBL or
        the Materials Project) that link to this table via a `substance` column.

        Only installed apps are included, so this list depends on your settings.
        """
        return [
            relation
            for relation in cls._meta.related_objects
            if relation.one_to_many
            and relation.field.name == "substance"
            and issubclass(relation.related_model, ThirdPartyData)
        ]

    def get_linked_entries(self, include_empty: bool = False) -> dict[str, list]:
        """
        Gives the ids of all third-party dataset entries linked to this substance.

        Args:
            include_empty: Whether to include tables that have no linked entries.

        Returns:
            A dictionary of table names (e.g. "ChemblMolecule") mapped to a list
            of linked entry ids.
        """
        linked_entries = {}
        for relation in self.linked_dataset_relations:
            table = relation.related_model
            entry_ids = list(
                table.objects.filter(substance_id=self.id).values_list("id", flat=True)
            )
            if entry_ids or include_empty:
                linked_entries[table.table_name] = entry_ids
        return linked_entries

    @classmethod
    def get_linked_entries_bulk(
        cls,
        substance_ids: list[str],
    ) -> dict[str, dict[str, list]]:
        """
        Gives the ids of all third-party dataset entries linked to each of the
        given substances.

        This makes one query per dataset table (rather than per substance), so
        it should be used instead of `get_linked_entries` when working with
        many substances.

        Args:
            substance_ids: The ids of the substances to search for.

        Returns:
            A dictionary of substance ids mapped to dictionaries of table names
            and linked entry ids (same format as `get_linked_entries`).
            Substances without any linked entries are given an empty dictionary.
        """
        linked_entries = {substance_id: {} for substance_id in substance_ids}
        for relation in cls.linked_dataset_relations:
            table = relation.related_model
            entries = table.objects.filter(substance_id__in=substance_ids).values_list(
                "substance_id", "id"
            )
            for substance_id, entry_id in entries:
                linked_entries[substance_id].setdefault(table.table_name, [])
                linked_entries[substance_id][table.table_name].append(entry_id)
        return linked_entries

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
        Generates an ID at the given level that is not already in use (in
        either this table or the `SubstanceDatastore`).
        """
        from ..datastores import SubstanceDatastore

        return SubstanceDatastore.generate_unique_ids(count=1, level=level)[0]

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
            value = int(char) if char.isdigit() else cls._LETTERS.index(char)
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

    # REGISTRATION

    # New substances are registered with `SubstanceDatastore.get_or_create_ids`
    # (the single entry point for all registration), which uses the helpers
    # below to save them in this table.

    @classmethod
    def _bulk_create_rows(cls, rows: list[dict]):
        """
        Saves new substances to this table, along with their molecule and
        crystal structure.

        Each row has the substance's columns, plus its `molecule` (a toolkit
        `Molecule`, a str such as SMILES, or None), the `inchi_key` of that
        molecule (or None), and its crystal `structure` (anything that
        `Structure.from_toolkit` accepts, or None).

        Existing molecules with the same inchi key are reused, and new rows
        that share an inchi key also share one new database molecule. Strings
        are only parsed if a new database molecule is needed.
        """
        molecules = {row["id"]: row["molecule"] for row in rows if row["molecule"]}
        existing = dict(
            Molecule.objects.filter(
                inchi_key__in={row["inchi_key"] for row in rows} - {None}
            ).values_list("inchi_key", "id")
        )

        # molecules without an inchi key can't be matched, so are grouped by
        # their substance ID instead
        groups = {row["id"]: row["inchi_key"] or row["id"] for row in rows}
        new_molecules = {}  # group --> new database molecule
        for substance_id, molecule in molecules.items():
            group = groups[substance_id]
            if group not in existing and group not in new_molecules:
                new_molecules[group] = Molecule.from_toolkit(
                    molecule=ToolkitMolecule.from_dynamic(molecule)
                )
        Molecule.objects.bulk_create(new_molecules.values())

        # add fingerprints to the new molecules (calculated by postgres)
        if new_molecules and settings.postgres_rdkit_extension:
            Molecule.populate_fingerprint_database(
                ids=[m.id for m in new_molecules.values()]
            )

        structures = {
            row["id"]: Structure.from_toolkit(structure=row["structure"])
            for row in rows
            if row["structure"]
        }
        Structure.objects.bulk_create(structures.values())

        cls.objects.bulk_create(
            [
                cls(
                    **{
                        k: v
                        for k, v in row.items()
                        if k not in ("molecule", "inchi_key", "structure")
                    },
                    molecule_id=(
                        existing.get(groups[row["id"]])
                        or new_molecules[groups[row["id"]]].id
                        if row["id"] in molecules
                        else None
                    ),
                    structure=structures.get(row["id"]),
                )
                for row in rows
            ]
        )

    @classmethod
    def _hydrate(cls, substance_ids: list[str]):
        """
        Copies substances that only exist in the `SubstanceDatastore` into this
        table (along with their molecule and crystal structure), so that other
        tables can link to them. IDs that are already in this table are skipped.

        Substances that these point to (via `parent` or `replaced_by`) are
        copied too.

        Raises:
            ValueError: if any IDs are not found in either location.
        """
        from ..datastores import SubstanceDatastore

        missing = set(substance_ids) - SubstanceDatastore.get_postgres_ids(
            substance_ids
        )
        if not missing:
            return

        # only the columns we copy over are loaded (e.g. not fingerprints)
        field_names = set(cls.get_column_names(id_mode=True))
        rows = []
        if SubstanceDatastore.chunk_files:
            columns = [
                c
                for c in SubstanceDatastore.schema().names()
                if c in field_names or c in ("smiles", "inchi_key", "structure")
            ]
            rows = (
                SubstanceDatastore.filter(id__in=list(missing))
                .select(columns)
                .collect()
                .to_dicts()
            )
        not_found = missing - {row["id"] for row in rows}
        if not_found:
            raise ValueError(f"Substances not found: {sorted(not_found)}")

        # the foreign keys need these to exist first
        linked_ids = {
            row.get(c) for row in rows for c in ("parent_id", "replaced_by_id")
        }
        cls._hydrate(list(linked_ids - missing - {None}))

        cls._bulk_create_rows(
            [
                {k: v for k, v in row.items() if k in field_names}
                | dict(
                    molecule=row["smiles"],
                    inchi_key=row["inchi_key"],
                    structure=row.get("structure"),
                )
                for row in rows
            ]
        )
        # these entries already match the datastore. This is set afterwards
        # (rather than in the constructor) because `updated_at` is set on
        # save, which would otherwise make it newer and so mark it unsynced
        cls.objects.filter(id__in=missing).update(datastore_synced_at=timezone.now())

    # -------------------------------------------------------------------------

    # ID CHANGES

    # Substance IDs are never deleted or reused. Instead, retired IDs are kept
    # as tombstones (`is_delisted=True`) that redirect to their successor via
    # `replaced_by`, and every change is logged in `SubstanceIdChange`. All
    # changes should go through the methods below so that linked tables and
    # the log stay consistent.
    #
    # Substances that are only in the `SubstanceDatastore` are first copied
    # into this table (see `_get_active`).

    @property
    def id_changes(self):
        """
        All logged ID changes that involve this substance, oldest first.
        """
        return SubstanceIdChange.objects.filter(
            Q(old_id=self.id) | Q(new_id=self.id)
        ).order_by("created_at")

    @classmethod
    def resolve_id(cls, substance_id: str) -> str:
        """
        Gives the current ID for the given one, following any merges or
        promotions. IDs that are active (or not found) are returned unchanged.
        """
        from ..datastores import SubstanceDatastore

        row = cls.objects.filter(id=substance_id).values("replaced_by_id").first()
        if not row and SubstanceDatastore.chunk_files:
            # not in this table, so check the full catalog
            df = (
                SubstanceDatastore.filter(id=substance_id)
                .select("replaced_by_id")
                .collect()
            )
            row = df.to_dicts()[0] if len(df) else None
        return (row and row["replaced_by_id"]) or substance_id

    @classmethod
    def _repoint_references(cls, old_ids: list[str], new_id: str):
        """
        Moves everything that links to the old substances over to the new
        one. This includes all foreign keys (e.g. batches, child substances,
        and third-party dataset entries) and many-to-many links (e.g. mixtures
        and projects) from any installed app.
        """

        # foreign keys from other tables (and from this table, e.g. `parent`
        # and `replaced_by`, which keeps redirects pointing to the newest ID)
        for model, column in cls._get_fk_links():
            entries = model.objects.filter(**{f"{column}__in": old_ids})
            updates = {column: new_id}
            if model is cls:
                entries = entries.exclude(id=new_id)
                updates["datastore_synced_at"] = None
            entries.update(**updates)

        # the new substance can't be its own parent or replacement
        cls.objects.filter(id=new_id, parent_id__in=old_ids).update(
            parent=None,
            datastore_synced_at=None,
        )

        # many-to-many links, both those defined on this table (e.g. projects)
        # and those pointing to it (e.g. mixtures). We delete + recreate the
        # links because the new substance may already have some of them.
        for through, substance_column, other_column in cls._get_m2m_links():
            links = through.objects.filter(**{f"{substance_column}__in": old_ids})
            other_ids = set(links.values_list(other_column, flat=True))
            links.delete()
            through.objects.bulk_create(
                [
                    through(**{substance_column: new_id, other_column: other_id})
                    for other_id in other_ids
                ],
                ignore_conflicts=True,
            )

    @classmethod
    def _get_fk_links(cls) -> list[tuple]:
        """
        Gives every foreign key to this table, from any installed app.

        Returns:
            A list of (model, substance id column), e.g. (Batch, "substance_id").
        """
        return [
            (relation.related_model, relation.field.attname)
            for relation in cls._meta.related_objects
            if relation.one_to_many
        ]

    @classmethod
    def _get_m2m_links(cls) -> list[tuple]:
        """
        Gives every many-to-many link to this table, both those defined on
        this table (e.g. projects) and those pointing to it (e.g. mixtures).

        Returns:
            A list of (through model, substance id column, other id column).
        """
        fields = [
            (field, field.m2m_field_name(), field.m2m_reverse_field_name())
            for field in cls._meta.many_to_many
        ] + [
            (
                relation.field,
                relation.field.m2m_reverse_field_name(),
                relation.field.m2m_field_name(),
            )
            for relation in cls._meta.related_objects
            if relation.many_to_many
        ]
        return [
            (field.remote_field.through, f"{substance_column}_id", f"{other_column}_id")
            for field, substance_column, other_column in fields
        ]

    @classmethod
    def get_referenced_ids(cls, substance_ids: list[str]) -> set[str]:
        """
        Gives which of the given substances are linked to by anything (e.g.
        batches, mixtures, projects, dataset entries, or other substances).
        These must stay in this table.
        """
        links = cls._get_fk_links() + [
            (through, substance_column)
            for through, substance_column, _ in cls._get_m2m_links()
        ]
        referenced = set()
        for model, column in links:
            referenced.update(
                model.objects.filter(**{f"{column}__in": substance_ids}).values_list(
                    column, flat=True
                )
            )
        return referenced

    @classmethod
    def _get_active(cls, substance_ids: list[str]) -> list["Substance"]:
        """
        Loads the given substances, raising an error if any are missing or
        already delisted. Substances that are only in the datastore are
        copied into this table first.
        """
        cls._hydrate(substance_ids)
        substances = list(cls.objects.filter(id__in=substance_ids))
        delisted = [s.id for s in substances if s.is_delisted]
        if delisted:
            raise ValueError(f"Substances are already delisted: {delisted}")
        return substances

    @classmethod
    def _hydrate_redirects(cls, substance_ids: list[str]):
        """
        Copies retired IDs that redirect to any of the given ones into this
        table, so that `_repoint_references` can update them (and there is
        never a chain of redirects). These are found with the
        `SubstanceIdChange` log rather than by scanning the datastore.
        """
        sources = set()
        frontier = set(substance_ids)
        while frontier:
            frontier = (
                set(
                    SubstanceIdChange.objects.filter(
                        new_id__in=frontier,
                        change_type__in=["merge", "promote"],
                    ).values_list("old_id", flat=True)
                )
                - sources
            )
            sources |= frontier
        cls._hydrate(list(sources))

    @classmethod
    def merge(
        cls,
        substance_ids: list[str],
        into: str,
        reason: str = None,
        matching_version: str = None,
    ) -> str:
        """
        Merges duplicate substances into a single one.

        All batches, mixtures, dataset entries, etc. of the duplicates are
        moved to the `into` substance, and the duplicates are delisted with
        `replaced_by` pointing to it.

        In most cases, `into` should be the most widely used ID (e.g. the
        oldest one, or the one with the lowest ID level).

        Args:
            substance_ids: The IDs of the duplicate substances to retire.
            into: The ID of the substance to keep.
            reason: Why the substances are being merged.
            matching_version: The version of the matching rules that found
                these duplicates (if any).

        Returns:
            The ID of the kept substance (i.e. `into`).
        """
        old_ids = [i for i in set(substance_ids) if i != into]
        with transaction.atomic():
            cls._get_active(old_ids + [into])
            cls._hydrate_redirects(old_ids)
            cls._repoint_references(old_ids, into)
            cls.objects.filter(id__in=old_ids).update(
                is_delisted=True,
                replaced_by_id=into,
                datastore_synced_at=None,
            )
            SubstanceIdChange.objects.bulk_create(
                [
                    SubstanceIdChange(
                        change_type="merge",
                        old_id=old_id,
                        new_id=into,
                        reason=reason,
                        matching_version=matching_version,
                    )
                    for old_id in old_ids
                ]
            )
        return into

    @classmethod
    def promote(
        cls,
        substance_id: str,
        level: int = 1,
        reason: str = None,
    ) -> str:
        """
        Moves a substance to a new ID at a different level. For example, a
        virtual level 2 compound that has been synthesized can be promoted to
        level 1.

        The substance (and everything linked to it) is copied to the new ID,
        and the old ID is delisted with `replaced_by` pointing to the new one.

        Args:
            substance_id: The ID of the substance to promote.
            level: The ID level to move the substance to.
            reason: Why the substance is being promoted.

        Returns:
            The new substance ID.
        """
        if cls.get_id_level(substance_id) == level:
            raise ValueError(f"{substance_id} is already a level {level} ID")

        with transaction.atomic():
            substance = cls._get_active([substance_id])[0]
            cls._hydrate_redirects([substance_id])
            created_at = substance.created_at

            new_id = cls.generate_unique_id(level=level)
            substance.id = new_id
            substance.check_digit = cls.calculate_check_digit(new_id)
            substance.datastore_synced_at = None
            substance._state.adding = True
            substance.save(force_insert=True)
            # the registration date stays the same as the original
            cls.objects.filter(id=new_id).update(created_at=created_at)

            cls._repoint_references([substance_id], new_id)
            cls.objects.filter(id=substance_id).update(
                is_delisted=True,
                replaced_by_id=new_id,
                datastore_synced_at=None,
            )
            SubstanceIdChange.objects.create(
                change_type="promote",
                old_id=substance_id,
                new_id=new_id,
                reason=reason,
            )
        return new_id

    @classmethod
    def split(
        cls,
        substance_id: str,
        entries: list[dict],
        reason: str = None,
        matching_version: str = None,
    ) -> list[str]:
        """
        Registers more specific substances that were previously covered by
        a single ID (e.g. stereoisomers or polymorphs that were not told apart
        by older matching rules).

        The original ID is kept and becomes the `parent` of the new substances,
        so existing references to it stay valid (just less specific). Nothing
        linked to the original (e.g. batches) is moved, as only a person can
        say which new substance each batch actually is.

        Args:
            substance_id: The ID of the substance being split.
            entries: The new substances, in the same format as
                `SubstanceDatastore.get_or_create_ids`. Substances that are
                already registered give their existing ID and are left
                unchanged.
            reason: Why the substance is being split.
            matching_version: The version of the matching rules that led to
                the split (if any).

        Returns:
            The substance IDs of each entry (in the same order).
        """
        from ..datastores import SubstanceDatastore

        with transaction.atomic():
            cls._get_active([substance_id])
            new_ids = SubstanceDatastore.get_or_create_ids(
                [dict(parent_id=substance_id, **entry) for entry in entries],
                level=cls.get_id_level(substance_id),
            )
            SubstanceIdChange.objects.bulk_create(
                [
                    SubstanceIdChange(
                        change_type="split",
                        old_id=substance_id,
                        new_id=new_id,
                        reason=reason,
                        matching_version=matching_version,
                    )
                    for new_id in dict.fromkeys(new_ids)  # unique, keeps order
                    if new_id != substance_id
                ]
            )
        return new_ids

    @classmethod
    def delist(
        cls,
        substance_id: str,
        reason: str = None,
    ):
        """
        Removes a substance from the catalog without a replacement (e.g. a
        junk entry or typo). The ID is kept as a tombstone so that it is
        never reused. Use `merge` instead if the substance is a duplicate.

        Args:
            substance_id: The ID of the substance to delist.
            reason: Why the substance is being delisted.
        """
        with transaction.atomic():
            cls._get_active([substance_id])
            cls.objects.filter(id=substance_id).update(
                is_delisted=True,
                datastore_synced_at=None,
            )
            SubstanceIdChange.objects.create(
                change_type="delist",
                old_id=substance_id,
                reason=reason,
            )

    # -------------------------------------------------------------------------
