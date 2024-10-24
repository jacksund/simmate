# -*- coding: utf-8 -*-

from rich.progress import track

from simmate.toolkit import Molecule


class Filter:
    """
    Abstract base class for filtering a list of molecules based on some criteria.

    At a minimum, subclasses must define either...
        1. a custom `check` method and set `is_atomic` True
        2. a custom `_check_serial` method and keep `is_atomic` False
    """

    is_atomic: bool = False
    """
    Whether the filter can be applied to individual entries.
    
    For some cases, a filter may depend on the makeup of all the molecules 
    provided -- rather than applying a check to individual molecules. These 
    cases should have 'is_atomic' set to False.
    
    For example, a filter that 'keep molecules under a weight of 100 g/mol' 
    is atomic, but a filter that says 'take the top 10% of molecules ranked 
    by weight' is NOT atomic.
    """

    @classmethod
    def check(cls, molecule: Molecule, **kwargs) -> bool:
        """
        "Filters" a single molecule which is really just a check that returns
        a true or false. Where possible, use the `filter` method instead as it
        is more robust and provides more features
        """
        # by default we assume there is a custom _check_serial method and call that
        if not cls.is_atomic:
            raise Exception(
                "This is NOT an atomic filter, which means you can not check individual"
                "molecules. Use the 'filter' method instead."
            )
        return cls._check_serial(molecules=[molecule], **kwargs)[0]

    @classmethod
    def filter(
        cls,
        molecules: list[Molecule],
        return_mode: str = "molecules",  # other options are "booleans" and "count"
        inverse: bool = False,
        parallel: bool = False,
        **kwargs,
    ) -> list:
        """
        Filters a list of molecules in a serial or parallel manner.
        """
        if not parallel:
            keep_list = cls._check_serial(molecules, **kwargs)
        else:
            if not cls.is_atomic:
                # !!! Is there an example algo where is_atomic=False, but it
                # can be ran in parallel? If so, I'd need to add `allow_parallel`
                raise Exception(
                    "This filtering method is not atomic and cannot be ran in parallel"
                )
            keep_list = cls._check_parallel(molecules, **kwargs)

        if inverse:
            # flips each True/False in the keep_list
            keep_list = [not k for k in keep_list]

        if return_mode == "count":
            # count num of True
            return sum(keep_list)
        elif return_mode == "booleans":
            return keep_list
        elif return_mode == "molecules":
            # return only Molecules that are True in keep_list
            return [mol for keep, mol in zip(keep_list, molecules) if keep]
        else:
            raise Exception(f"Unknown return mode: {return_mode}")

    @classmethod
    def _check_serial(
        cls,
        molecules: list[Molecule],
        progress_bar: bool = False,
        **kwargs,
    ) -> list[bool]:
        """
        Filters a list of molecules in serial
        (so one at a time on a single core).
        """
        features_list = []
        for molecule in track(molecules, disable=not progress_bar):
            features = cls.check(molecule, **kwargs)
            features_list.append(features)
        return features_list

    @classmethod
    def _check_parallel(
        cls,
        molecules: list[Molecule],
        batch_size: int = 10000,
        use_serial_batches: bool = False,
        batch_size_serial: int = 500,
        **kwargs,
    ) -> list[bool]:
        """
        Filters a list of molecules in parallel.
        """
        # Use this method to help. Maybe write a utility function for batch
        # submitting and serial-batch submitting to dask too.
        # https://github.com/jacksund/simmate/blob/17d926fe5ee8f183240a4526982b4d7fd5d7042b/src/simmate/toolkit/creators/structure/base.py#L67
        raise NotImplementedError("This method is still being written")

    @classmethod
    def from_preset(cls, preset: str, molecules: list[Molecule], **kwargs):
        if preset == "many-smarts":
            from simmate.toolkit import Molecule
            from simmate.toolkit.filters import ManySmarts as ManySmartsFilter

            smarts_strs = kwargs.pop("smarts_strs", None)
            if not smarts_strs:
                raise ValueError(
                    "smiles_strs is required as an input for this method. "
                    "Provide a list of SMARTS strings."
                )
            smiles_mols = [Molecule.from_smarts(s) for s in smarts_strs]
            return ManySmartsFilter.filter(
                molecules=molecules,
                smarts_list=smiles_mols,
                **kwargs,
            )
        else:
            raise Exception(f"Unknown present provided: {preset}")
