# Common Analyses

!!! important
    This page provides a concise list of available features, grouped by function. Detailed descriptions of each property can be found in the `API` section.

!!! tip
    If you're searching for analyses such as clustering, similarity, or chemspace mapping, you'll find them in the "many molecule" analyses section. This page is dedicated to single-molecule analysis.

--------------------------------------------------------------------------------

## Overview

Most analyses are implemented as Python methods, accepting a range of input arguments and formats.

For instance, you can call a method like this:

``` python
query = "[CX2]#[CX2]"
is_alkyne = molecule.is_smarts_match(query)
```

It's recommended to review the documentation for each method before using it. This page serves as a quick reference to help you identify available methods.

--------------------------------------------------------------------------------

!!! danger
    The methods are not yet grouped, so they are listed in no particular order for the time being.

- `get_r_groups`
- `get_fragments`
- `is_smarts_match`
- `num_smarts_match`
- `num_substructure_matches`
- `get_num_atoms_of_atomic_number`
- `get_num_atoms_of_atomic_symbols`
- `get_stereocenters`
