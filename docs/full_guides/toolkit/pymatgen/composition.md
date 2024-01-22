# PyMatGen Compositions

!!! important
    This page provides a concise list of available properties and methods, grouped by topic. 
    
    Refer to [Pymatgen's API docs](https://pymatgen.org/pymatgen.core.html) for detailed descriptions.

--------------------------------------------------------------------------------

## Introduction

To access the `Composition` objects from a `Structure`:

``` python
comp = structure.composition
```

The `composition` property is also available for  `Molecule`, `Cluster`, `Interface`, and more.

!!! warning
    a `Composition` object can come from a variety of sources. For example, a composition can be for an entire `Structure` OR just a single chemical component (such as a `Molecule`, `Cluster`, `Interface`, etc.).

--------------------------------------------------------------------------------

## Composition Loading

- `from_dict`
- `from_weight_dict`

--------------------------------------------------------------------------------

## Composition Exporting

- `as_dict`
- `copy`
- `to_data_dict`
- `to_html_string`
- `to_json`
- `to_latex_string`
- `to_pretty_string`
- `to_reduced_dict`
- `to_unicode_string`
- `to_weight_dict`

--------------------------------------------------------------------------------

## Basic Properties

- `alphabetical_formula`
- `anonymized_formula`
- `average_electroneg`
- `chemical_system`
- `element_composition`
- `elements`
- `formula`
- `fractional_composition`
- `iupac_formula`
- `hill_formula`
- `reduced_composition`
- `reduced_formula`
- `special_formulas`
- `total_electrons`
- `values`
- `weight`
- `num_atoms`

--------------------------------------------------------------------------------

## Analysis Methods

- `amount_tolerance`
- `almost_equals`
- `contains_element_type`
- `is_element`
- `valid`
- `get_atomic_fraction`
- `get_el_amt_dict`
- `get_integer_formula_and_factor`
- `get_reduced_composition_and_factor`
- `get_reduced_formula_and_factor`
- `get_wt_fraction`
- `oxi_prob`
- `oxi_state_guesses`
- `ranked_compositions_from_indeterminate_formula`

--------------------------------------------------------------------------------

## Dict-like Utils

- `get`
- `items`
- `keys`

--------------------------------------------------------------------------------

## Charge Utils

- `add_charges_from_oxi_state_guesses`
- `allow_negative`
- `remove_charges`
- `replace`

--------------------------------------------------------------------------------

## JSON Utils

- `unsafe_hash`
- `validate_monty_v1`
- `validate_monty_v2`

--------------------------------------------------------------------------------
