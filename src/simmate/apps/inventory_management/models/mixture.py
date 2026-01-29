# -*- coding: utf-8 -*-

from simmate.database.base_data_types import DatabaseTable, table_column

from .substance import Substance


class Mixture(DatabaseTable):

    class Meta:
        db_table = "inventory_management__mixtures"

    html_display_name = "Mixtures"
    html_description_short = (
        "Mixtures are the combination of two or more substances. "
        "For example, a solution would be a mixture of two substances: NaCl and water. "
        "This table includes mixtures of both specified and unspecified ratios, "
        "meaning 'salt water' and '0.1M salt water' can be separate entries."
    )

    # -------------------------------------------------------------------------

    # disable cols
    source = None

    mixture_type_options = [
        "solution",  # solid in liquid mix
        "liquid mix",
        "gas mix",
        "solid mix",
        "other",
    ]
    mixture_type_type = table_column.CharField(
        max_length=15,
        blank=True,
        null=True,
    )

    description = table_column.TextField(blank=True, null=True)

    # -------------------------------------------------------------------------

    common_name = table_column.CharField(max_length=255, blank=True, null=True)

    synonyms = table_column.JSONField(blank=True, null=True, default=list)

    # -------------------------------------------------------------------------

    substances = table_column.ManyToManyField(
        Substance,
        blank=True,
        db_table="inventory_management__mixture_components",
        related_name="mixtures",
    )

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
