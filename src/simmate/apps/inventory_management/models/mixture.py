# -*- coding: utf-8 -*-

import random

from simmate.database.core import DatabaseTable, table_column

from .substance import Substance


class Mixture(DatabaseTable):
    """
    A defined combination of substances, such as a stock solution or a
    solvent blend.

    Components are listed loosely via `substances`, and any details on how they
    are combined (e.g. concentrations or ratios) go in the `description`.
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
    (e.g. "BCDF-123"). This makes the ID recognizable and acts as a typo check.
    """

    @property
    def display_id(self) -> str:
        """
        The human-readable ID to show in user interfaces and exports.
        """
        return f"{self.id_prefix}-{self.id}"

    @classmethod
    def get_by_display_id(cls, display_id: str):
        """
        Loads a mixture using its display ID (e.g. "BCDF-123"). Raises
        `Mixture.DoesNotExist` if the ID is malformed, if no mixture has that
        number, or if the prefix does not match the number.
        """
        prefix, _, number = display_id.strip().upper().partition("-")
        if not number.isdigit():
            raise cls.DoesNotExist(f"Invalid mixture ID: '{display_id}'")
        return cls.objects.get(id=int(number), id_prefix=prefix)

    # -------------------------------------------------------------------------

    mixture_type_options = [
        "solution",  # solid in liquid mix
        "liquid mix",
        "gas mix",
        "solid mix",
        "other",
    ]
    mixture_type = table_column.CharField(
        max_length=15,
        blank=True,
        null=True,
    )
    """
    The kind of mixture this is. Must be one of `mixture_type_options`.
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
        db_table="inventory_management__mixture_components",
        related_name="mixtures",
    )
    """
    The substances that make up this mixture.
    """

    # I could get more detailed with the components of a mixture, but as things
    # get more complex, it in some ways get more rigid (e.g. a unique mixture
    # can't be represented), and it also gets more cumbersome for users inputing
    # stuff. I currently opt for users to just list what is in the mixture
    # and then add a description of any extra details they need like...
    #
    #   '0.1 M solution of ___ in 3:1 solvent mix of methanol:water with 1 mg catalyst'
    #
    # Rather than trying to fit every possible description into components like...
    #
    #   class MixtureComponent:
    #     mixture
    #     substance
    #     percentage
    #     concentration
    #     relative_ratio
    #     component_type_options =[
    #         "solvent",
    #         "co-solvent",
    #         "solute",
    #         # if it is a reaction/reagent
    #         "starting_material",
    #         "product",
    #         "by-product",
    #         "impurity",
    #         "catalyst",
    #         "coupling_agent",
    #         "ligand",
    #         "phase_transfer_agent",
    #         #
    #         "other",
    #     ]

    # -------------------------------------------------------------------------
