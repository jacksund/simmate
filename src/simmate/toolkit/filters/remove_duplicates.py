# -*- coding: utf-8 -*-

from rich.progress import track

from simmate.toolkit import Molecule

from .base import Filter


class RemoveDuplicates(Filter):
    """
    Given a list of molecules, this will identify/remove duplicate molecules
    as based on Inchi Key matches. This means duplicates are determined by
    structure alone -- not 2D or 3D coordinates.

    When `inverse=True`, this filter effectively becomes `IdentifyDuplicates`
    and it will return all extras.

    Example use:
    ```
    molecules_filtered = RemoveDuplicates.filter(molecules)
    ```
    """

    @classmethod
    def _check_serial(
        cls,
        molecules: list[Molecule],
        progress_bar: bool = False,
        **kwargs,
    ) -> list[bool]:
        """
        Identifies duplicates in a list of molecules. The first occurance of
        each molecule with yield True, while following duplicates will give
        False -- indicating that they should be removed.
        """
        keep_list = []
        inchi_key_ref = []
        for molecule in track(molecules, disable=not progress_bar):
            inchi_key = molecule.to_inchi_key()
            if inchi_key not in inchi_key_ref:
                inchi_key_ref.append(inchi_key)
                keep_list.append(True)
            else:
                keep_list.append(False)
        return keep_list
