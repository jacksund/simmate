# -*- coding: utf-8 -*-


def _init_common_class(self, class_str):

    # CREATORS
    if class_str in [
        "RandomSymStructure",
        "PyXtalStructure",
    ]:
        creator_class = getattr(creation_module, class_str)
        return creator_class(self.composition)

    # TRANSFORMATIONS
    elif class_str in [
        "from_ase.Heredity",
        "from_ase.SoftMutation",
        "from_ase.MirrorMutation",
        "from_ase.LatticeStrain",
        "from_ase.RotationalMutation",
        "from_ase.AtomicPermutation",
        "from_ase.CoordinatePerturbation",
    ]:
        # all start with "from_ase" so I assume that import for now
        ase_class_str = class_str.split(".")[-1]
        mutation_class = getattr(transform_module, ase_class_str)
        return mutation_class(self.composition)

    # These are commonly used single-shot sources
    elif class_str == "prototypes_aflow":
        pass  # TODO
    elif class_str == "substitution":
        pass  # TODO
    elif class_str == "third_party_structures":
        pass  # TODO
    elif class_str == "third_party_substitution":
        pass  # TODO

    else:
        raise Exception(
            f"{class_str} is not recognized as a common input. Make sure you"
            "don't have any typos, and if you are using a custom class, provide"
            "your input as an object."
        )
