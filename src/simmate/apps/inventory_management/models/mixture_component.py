from simmate.database.core import DatabaseTable, table_column


class MixtureComponent(DatabaseTable):
    """
    A substance within a `Mixture`, along with its role and amount.

    This is the link table behind `Mixture.substances`, so components can be
    listed loosely (e.g. with `mixture.substances.set([...])` or the
    `substances__ids` form input) and have their details filled in later.
    All detail columns are optional, and anything they don't capture should
    go in the mixture's `description`.

    Available from a mixture via `components` and from a substance via
    `mixture_components`.
    """

    class Meta:
        db_table = "inventory_management__mixture_components"
        unique_together = [("mixture", "substance")]

    # -------------------------------------------------------------------------

    mixture = table_column.ForeignKey(
        "Mixture",
        on_delete=table_column.CASCADE,
        related_name="components",
    )
    """
    The mixture that this component belongs to.
    """

    substance = table_column.ForeignKey(
        "Substance",
        on_delete=table_column.CASCADE,
        related_name="mixture_components",
    )
    """
    The substance that this component is.
    """

    # -------------------------------------------------------------------------

    role_options = [
        "solvent",
        "co_solvent",
        "solute",
        "additive",  # e.g. stabilizers, preservatives, and dopants
        # if it is a reaction/reagent
        "starting_material",
        "product",
        "by_product",
        "impurity",
        "catalyst",
        "coupling_agent",
        "ligand",
        "phase_transfer_agent",
        "reagent",
        # formulations
        "active_ingredient",
        "adjuvant",
        #
        "other",
    ]
    role = table_column.CharField(max_length=25, blank=True, null=True)
    """
    The role this substance plays in the mixture. Must be one of
    `role_options`.

    This can be left empty when no role applies, such as for the isomers in
    an isomer mix.
    """

    amount = table_column.FloatField(blank=True, null=True)
    """
    How much of this substance is in the mixture, in `amount_units`.
    """

    amount_units_options = [
        "M",
        "mM",
        "uM",
        "mg/ml",
        "wt%",
        "vol%",
        "w/v%",
        "mol%",
        "ppm",
        "equiv",
        "parts",  # relative ratios (e.g. 3 and 1 for a 3:1 mix)
    ]
    amount_units = table_column.CharField(max_length=10, blank=True, null=True)
    """
    The units for `amount`. Must be one of `amount_units_options`.
    """

    # -------------------------------------------------------------------------
