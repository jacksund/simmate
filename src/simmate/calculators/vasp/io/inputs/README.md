

## INCAR NOTES

Pymatgen has an incar_parameters.json file which lists all of the possible INCAR
options. This is only ever used by vasp in the Incar.check_params method, which
does the follow:
"""
        Raises a warning for nonsensical or non-existant INCAR tags and
        parameters. If a keyword doesn't exist (e.g. theres a typo in a
        keyword), your calculation will still run, however VASP will igore the
        parameter without letting you know, hence why we have this Incar method.
"""
https://github.com/materialsproject/pymatgen/blob/32cad282bc919965cd2d6014be25a5459fe5a670/pymatgen/io/vasp/inputs.py#L971

This is nice, but I don't think a highlevel python package (like Simmate) should
keep track of this. This would mean someone has to stay on top of all of a
calculator's changes/additions/deletions to the incar, which can be overwhelming
for many calculators (especially DFT ones -- VASP alone has >350 inputs parameters!).
Pymatgen, Custodian, and Atomate never even use this .check_params() method, which
may be an oversight on their part, or even a choice done for speed reasons. Either
way, I think we lose very little by leaving this out.

Removed as_dict and from_dict methods for now. Will reimplement later.

Removed __setitem__ method as this only removed leading and trailing whitespace
from the parameter or value (e.g. "  ENCUT " --> "ENCUT"). This can be done
in the from_file method as that's the only place that's ever relevent.

Removed from_string method. This should be done inside the from_file method. Users
should always init their own Incar object or read from an INCAR file. There's
no good reason for a user to read and init the class from a string. The argument
to have it is for testing only (pytest).

Removed get_string. Pymatgen makes this separate from __str__ method for
"pretty printing" options that just use the tabulate option. I remove the dependency
on tabulate and just merge this into the __str__ function. Also the option to
order the keys alphabetically is removed and assumed False! I prefer to leave
keys in the order the user (or class) provided them, which often prefers logical
ordering over alphabetical.

proc_val is renamed to str_to_datatype.


## POSCAR NOTES

Rather than having a Poscar instance for each Structure object as pymatgen does,
I want the Poscar to be a Converter. Therefore, this is a class that Structures
pass through, rather than being loaded+initialized+written. For example, you would
use the following code to write a series of Structures to POSCAR files:
    in pymatgen... 
        for structure in structures:
            poscar = Poscar(structure)
            poscar.write_file(filename)
    in simmate...
        for structure in structures:
            Poscar.write_file(structure, filename)
This may seem trivial, but it helps a lot with speed, and it also allows us to
write a ton of Structures to files in parallel with Dask. For example:
    Poscar.write_many_files([structure1, structure2, ...], [filename1, filename2, ...])

set_temperature method is removed. I think this is a general method for structures
and isn't specific to VASP. Therefore, this code should exist elsewhere. I need to
revisit this code when I write velocity type methods or the Structure object.

sort_structure parameter is removed. If you want the structure's sites to be sorted,
this should be done before passing to the POSCAR class.

__setattr__ method is removed. This looks like a spin-off of Structure.add_site_property()
method and doesn't belong in this class, but in the Structure class.

All of the property attributes are removed because this is now a Converter
class and we no longer initialize a structure-specific Poscar.

site_symbols and natoms methods are removed. These are easy one-liners when
implemented through the Composition class.

Removed as_dict and from_dict methods for now. Will reimplement later if it's
even needed for this Converter class.

__str__ method is removed. I could consider a to_string() method, but idk why
anyone would ever use it besides in-terminal testing.

Removed from_string method. This should be done inside the from_file method. Users
should always init their own Incar object or read from an INCAR file. There's
no good reason for a user to read and init the class from a string. The argument
to have it is for testing only (pytest).

In the from_file method, I do not check the POTCAR. Instead, Simmate users should
follow the most current POSCAR format that lists the element types on the 6th line
and/or at the end of each site's coordinates. This may cause issues if someone wants
to read a really old VASP format, but it's probably too much for Simmate to always
have legacy support for all the different calculators. It should be the current way,
or the highway. If someone wants to load old structures, they should write their
own script rather than muddying the code of Simmate. Also, thee is no "last-resort method"
like in pymatgen. If the user isn't following VASP guidlines, an error will be raised
or they should write their own method.

It doesn't look like pymatgen saves the selective dynamics tags to site_properties,
but I choose to.

The read_velocities function I left as a to-do item as I didn't understand the MD
formatting at a first glance, and I don't ever see an example of pymatgen, custodian,
or atomate ever using this tag anyways.

While I support loading a Poscar that has cartesian coordinates, I have users
write all files in fractional (direct). 
