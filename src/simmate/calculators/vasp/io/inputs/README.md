

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
