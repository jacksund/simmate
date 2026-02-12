
(experimental feature; advanced users only)
This parameter is a dictionary of sources that will be scheduled at a "steady-state", meaning there will always be a set number of individuals scheduled/running for this type of structure source. This should be defined as a dictionary where each is `{"source_name": percent}`. The percent determines the number of steady stage calculations that will be running for this at any given time. It will be a percent of the `nsteadystate` parameter, which sets the total number of individuals to be scheduled/running. For example, if `nsteadystate=40` and we add a source of `{"RandomSymStructure": 0.30, ...}`, this means 0.25*40=10 randomly-created individuals will be running/submitted at all times. The source can be from either the `toolkit.creator` or `toolkit.transformations` modules.

=== "yaml"
    ``` yaml
    singleshot_sources:
        RandomSymStructure: 0.30
        from_ase.Heredity: 0.30
        from_ase.SoftMutation: 0.10
        from_ase.MirrorMutation: 0.10
        from_ase.LatticeStrain: 0.05
        from_ase.RotationalMutation: 0.05
        from_ase.AtomicPermutation: 0.05
        from_ase.CoordinatePerturbation: 0.05
    ```
=== "toml"
    ``` toml
    [singleshot_sources]
    "RandomSymStructure": 0.30
    "from_ase.Heredity": 0.30
    "from_ase.SoftMutation": 0.10
    "from_ase.MirrorMutation": 0.10
    "from_ase.LatticeStrain": 0.05
    "from_ase.RotationalMutation": 0.05
    "from_ase.AtomicPermutation": 0.05
    "from_ase.CoordinatePerturbation": 0.05
    ```
=== "python"
    ``` python
    singleshot_sources = {
        "RandomSymStructure": 0.30,
        "from_ase.Heredity": 0.30,
        "from_ase.SoftMutation": 0.10,
        "from_ase.MirrorMutation": 0.10,
        "from_ase.LatticeStrain": 0.05,
        "from_ase.RotationalMutation": 0.05,
        "from_ase.AtomicPermutation": 0.05,
        "from_ase.CoordinatePerturbation": 0.05,
    }
    ```

Note: if your percent values do not sum to 1, they will be rescaled. When calculating `percent*nsteadystate`, the value will be rounded to the nearest integer.

We are moving towards accepting kwargs or class objects as well, but this is not yet allowed. For example, anything other than `percent` would be treated as a kwarg:

=== "toml"
    ``` toml
    [singleshot_sources.RandomSymStructure]
    percent: 0.30
    spacegroups_exclude: [1, 2, 3]
    site_generation_method: "MyCustomMethod"
    ```
