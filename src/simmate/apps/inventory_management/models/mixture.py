import random

from simmate.database.core import DatabaseTable, table_column

from .substance import Substance


class Mixture(DatabaseTable):
    """
    A defined combination of substances, such as a stock solution or a
    solvent blend.

    Components are listed via `substances`, and each can optionally be given
    a role and amount (see `components` and the `MixtureComponent` table).
    Any other details (e.g. how it was prepared) go in the `description`.
    Mixtures are identified by their `display_id` (e.g. "BCDF-123").
    """

    class Meta:
        db_table = "inventory_management__mixtures"

    # -------------------------------------------------------------------------

    # same convention as Substance IDs (no vowels or Y)
    _LETTERS = "BCDFGHJKLMNPQRSTVWXZ"

    @staticmethod
    def generate_id_prefix() -> str:
        """
        Generates a random 4-letter prefix for use as the `id_prefix`.
        """
        return "".join(random.choices(Mixture._LETTERS, k=4))

    id = table_column.BigAutoField(primary_key=True)
    """
    The auto-incrementing integer ID of the mixture. This is combined with
    `id_prefix` to give the `display_id`.
    """

    id_prefix = table_column.CharField(
        max_length=4,
        blank=True,
        null=True,
    )
    """
    Random 4-letter prefix shown with the integer `id` as the `display_id`
    (e.g. "BCDF-123"). This makes the ID recognizable and acts as a typo check
    when IDs are typed in (see `get_by_display_id`). Unlike other tables, this
    is set per row rather than being a static prefix for the whole table.
    """

    # -------------------------------------------------------------------------

    mixture_type_options = [
        "solution",
        "suspension",
        "emulsion",
        "liquid_mix",
        "gas_mix",
        "solid_mix",
        "isomer_mix",
        "reaction_mix",
        "formulation",
        "extract",
        "other",
    ]
    mixture_type = table_column.CharField(
        max_length=15,
        blank=True,
        null=True,
    )
    """
    The kind of mixture this is. Must be one of `mixture_type_options`.

    When more than one applies, pick the most specific (e.g. a formulation
    that is also a suspension is a `formulation`). For example:
        - `solution`: solutes (solids, liquids, or gases) dissolved in a
          solvent, typically at a set concentration (e.g. 1 M HCl in water)
        - `suspension`: undissolved solids in a liquid, including slurries
          and colloids (e.g. Pd/C in methanol or nanoparticle dispersions)
        - `emulsion`: droplets of one liquid in another that it does not
          mix with
        - `liquid_mix`: miscible liquids combined by ratio (e.g. solvent
          blends and eluents)
        - `isomer_mix`: isomers of a substance in any non-racemic ratio (e.g.
          xylenes or E/Z mixtures). Racemates are registered as a `Substance`
          instead.
        - `reaction_mix`: crude or in-progress reaction contents
    """

    description = table_column.TextField(blank=True, null=True)
    """
    A full description of the mixture, including any details not captured by
    `substances` (e.g. "0.1 M solution of ___ in 3:1 methanol:water").
    """

    # -------------------------------------------------------------------------

    common_name = table_column.CharField(max_length=255, blank=True, null=True)
    """
    The name that the mixture is most commonly referred to by.
    """

    synonyms = table_column.JSONField(blank=True, null=True, default=list)
    """
    A list of other names that the mixture is known by.
    """

    # -------------------------------------------------------------------------

    # TODO: If the mixture contains at least one stereoisomer
    # ├── Racemate (1:1 Enantiomeric Mixture)
    # ├── Enantiopure (Single Enantiomer)
    # └── Scalemic (Enriched, but not 1:1 or 100%)
    # OR... even enhanced stereochem that allows unknown. Might need separate
    # column or even table to store the clean & enhanced smiles/molfile for these

    # -------------------------------------------------------------------------

    substances = table_column.ManyToManyField(
        Substance,
        blank=True,
        through="MixtureComponent",
        related_name="mixtures",
    )
    """
    The substances that make up this mixture. The role and amount of each
    are stored on its `MixtureComponent` (available via `components`).
    """

    # Component details are kept optional, because requiring them would make
    # the table more rigid (not every mixture fits a fixed set of columns) and
    # more cumbersome to fill in. Users can just list what is in the mixture,
    # add roles and amounts where they are known, and describe anything else
    # in the `description`, such as...
    #
    #   '0.1 M solution of ___ in 3:1 solvent mix of methanol:water with 1 mg catalyst'

    # -------------------------------------------------------------------------
