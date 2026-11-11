def parse_container_description(text: str) -> dict:
    """
    Parses a plain-text description of a container's contents (e.g. "0.1M
    solution of NaCl in water") into the inputs of the inventory's "Register
    Container" form.

    Every key is optional, and anything that could not be parsed is None.
    Substances are given as either a substance ID or a SMILES.

    Example return:
    ``` python
    {
        "contents_type": "mixture",  # or "substance"
        # an ID or SMILES (only when contents_type is "substance")
        "substance": None,
        # only when contents_type is "mixture"
        "mixture": {
            "mixture_type": "solution",  # one of Mixture.mixture_type_options
            "common_name": "0.1 M NaCl in water",
            "description": "0.1 M solution of NaCl in water",
            "components": [
                {
                    "substance": "[Na+].[Cl-]",
                    "role": "solute",  # one of MixtureComponent.role_options
                    "amount": 0.1,
                    "amount_units": "M",  # one of MixtureComponent.amount_units_options
                },
                {
                    "substance": "O",
                    "role": "solvent",
                    "amount": None,
                    "amount_units": None,
                },
            ],
        },
        # any Batch columns (e.g. supplier, purity, or appearance)
        "batch": {"supplier": None, "purity": None},
        # any Container columns (e.g. initial_amount or amount_units)
        "container": {"initial_amount": None, "amount_units": None},
    }
    ```

    Args:
        text: The description to parse.

    Returns:
        The parsed form inputs (see the example above).
    """
    # TODO: replace this placeholder with a call to the llm (via `get_llm()`).
    # For now, this always gives the example above so that the form can be
    # tried out end to end.
    return {
        "contents_type": "mixture",
        "substance": None,
        "mixture": {
            "mixture_type": "solution",
            "common_name": "0.1 M NaCl in water",
            "description": "0.1 M solution of NaCl in water",
            "components": [
                {
                    "substance": "[Na+].[Cl-]",
                    "role": "solute",
                    "amount": 0.1,
                    "amount_units": "M",
                },
                {
                    "substance": "O",
                    "role": "solvent",
                    "amount": None,
                    "amount_units": None,
                },
            ],
        },
        "batch": {"supplier": None, "purity": None},
        "container": {"initial_amount": None, "amount_units": None},
    }
