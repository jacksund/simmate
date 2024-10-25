# -*- coding: utf-8 -*-

from rich.progress import track

from simmate.toolkit import Molecule

from .base import Filter


class RemoveMolecules(Filter):
    """
    Filters given a list of molecules and another list of molecule to remove.
    The filtering is based on Inchi Key matches, which means matches are
    determined by structure alone -- not 2D or 3D coordinates.

    When `inverse=True`, this filter effectively becomes `IdentifyMatches`
    and it will return all matches found in the first list.

    Example use:
    ```
    # both inputs should be a list of Molecule objects
    molecules_filtered = RemoveMolecules.filter(
        molecules=[...],
        molecules_to_remove=[...],
    )
    ```
    """

    @classmethod
    def _check_serial(
        cls,
        molecules: list[Molecule],
        molecules_to_remove: list[Molecule],
        progress_bar: bool = False,
        **kwargs,
    ) -> list[bool]:
        """
        Identifies duplicates in a list of molecules. The first occurance of
        each molecule with yield True, while following duplicates will give
        False -- indicating that they should be removed.
        """
        if isinstance(molecules_to_remove, list):
            keys_to_remove = [m.to_inchi_key() for m in molecules_to_remove]
        else:
            # See if we have MoleculeSearchResults from the database
            try:
                # query the full column of inchi_keys, which is faster
                # than downloading all molecules and then converting
                keys_to_remove = list(
                    molecules_to_remove.values_list("inchi_key", flat=True).all()
                )
            except:
                raise Exception(f"Unknown Input: {type(molecules_to_remove)}")

        keep_list = []
        for molecule in track(molecules, disable=not progress_bar):
            inchi_key = molecule.to_inchi_key()
            keep = True if inchi_key not in keys_to_remove else False
            keep_list.append(keep)

        return keep_list
