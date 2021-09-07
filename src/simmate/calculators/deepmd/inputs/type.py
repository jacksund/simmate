# -*- coding: utf-8 -*-

import os

import numpy


class DeepmdType:
    """
    This class works simply as a converter. You provide it a composition and it
    will write the deepmd "type.raw" and "type_map.raw" files for you.
    
    Note these files are very simple. The type map is just a list of elements
    and the type raw is our composition listing what each site is.
    """

    @staticmethod
    def to_files(
        composition, type_filename="type.raw", mapping_filename="type_map.raw"
    ):

        # first let's write the type_map file, which is just a list of elements
        with open(mapping_filename, "w") as file:
            for element in composition:
                file.write(str(element) + "\n")

        # Now we can write the type file while also establish the mapping.
        # Note the mapping is just the index (0, 1, 2, ...) of each element.
        with open(type_filename, "w") as file:
            for mapping_value, element in enumerate(composition):
                for i in range(int(composition[element])):
                    file.write(str(mapping_value) + "\n")
