# -*- coding: utf-8 -*-


class VaspSetup:

    # TODO to_dict, from_dict

    def write_input(self):
        # call Incar, Poscar, Potcar, and Kpoints classes' to_file methods.
        pass

    def from_directory(self):
        # call Incar, Poscar, Potcar, and Kpoints classes' from_file methods
        # and get's ALL the proper objects.
        pass

    # don't forget to look at the logic for generating Incar and Kpts in DictSet
