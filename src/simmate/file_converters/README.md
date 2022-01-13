
File Converters
---------------

> :warning: This module is at the planning stage so no code exists here yet.

I think this will be a good module to have io features that can't be added to a specific calculator or toolkit module. For example, cif/xyz files are universal standards, and not linked directly to a specific calculator. There are also third-party classes (e.g. pymatgen/ase/jarvis structures) which users may want to switch between.

I therefore plan for this module to be a one-stop place where users can convert between formats. For example, for simmate.file_converters.structures will have imports pointing toward vasp(POSCAR), castep, cif, pymatgen, ase, and all the different ways to represent a single crystal structure. Links between formats (e.g. vasp --> castep) will be done by first converting to a simmate.toolkit.base_data_types.Structure first.
