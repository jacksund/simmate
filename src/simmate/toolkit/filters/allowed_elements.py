# -*- coding: utf-8 -*-

from simmate.toolkit import Molecule

from .base import Filter


class AllowedElements(Filter):

    is_atomic = True

    @classmethod
    def check(
        cls,
        molecule: Molecule,
        elements: list[str] = ["H", "C", "O", "N", "S", "F"],
        mode: str = "include",  # exclude, include, include_all
    ) -> bool:
        molecule = Molecule.from_dynamic(molecule)
        if mode == "include":
            # only the element is allowed
            for element in molecule.elements:
                if element not in elements:
                    return False
            return True

        elif mode == "include_all":
            # the full element list must match *in full*. So all elements must be present
            elements_check = molecule.elements
            elements_check.sort()
            elements.sort()
            return elements == elements_check

        elif mode == "exclude":
            # *none* of the elements are allowed. if any is present, it fails
            for element in molecule.elements:
                if element in elements:
                    return False
            return True
