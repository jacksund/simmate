
## INCAR NOTES

For all other input types (POSCAR, KPOINTS, POTCAR), I write these as Converters
that take more generic objects such a Structure, KptGrid, and Potential and
converts them into the VASP format. Should I do the same with INCAR? I would
have a DftSettings or DftCalc class that the Incar would convert. This might
make settings used confusing for users. VASP user would have to understand the
mapping of ENCUT in Incar to energy_cutoff in DftCAlc, which I'm not sure would
help or hurt. My initial thought is this is great for new users or those that 
want to switch calculators, but bad for those that are experts in VASP and want
to update a single flag. For example, if a user wanted to change a workflow's
ISIF tag, they would first have to look up the respective tag. I don't
implement this for that reason.

Pymatgen has an incar_parameters.json file which lists all of the possible INCAR
options. This is only ever used by vasp in the Incar.check_params method, which
does the following:
```
Raises a warning for nonsensical or non-existant INCAR tags and
parameters. If a keyword doesn't exist (e.g. theres a typo in a
keyword), your calculation will still run, however VASP will igore the
parameter without letting you know, hence why we have this Incar method.
```
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


## KPOINTS NOTES

Removed as_dict and from_dict methods for now. Will reimplement later if it's
even needed for this Converter class.

For automatic generation of a kpts at a specific density, VASP now has a input
parameter "KSPACING" that should be used and they recommend against using the
automatic mode in the KPOINTS file. Thus this class should really only be used
when you're doing a bandstructure calculation and need to set the specific path
for your calculation. Still, I will support manual writing of KPOINTS files that
specify an automatic mesh, but rarely use it elsewhere. Instead I will always
perfer setting the kpoint denisty in the INCAR file.
VASP also indicates there are some cells where their KSPACING tag will not work
as described in the "Symmetry reduction of the mesh" section of the KPOINTS page.
I think such errors can be handled by a VaspHandler by doing one of the following:
- don't use the primitive cell, but the LLL reduced or conventional one instead
- set the grid to N1xN2xN3 where N1=N2=N3  
Thus I should still provide some support for writing a specific kpt grid. I can
also use the KGAMMA parameter to change this as well.

"automatic gamma density" is absorbed into "automatic density by volume"
functionality. It's also never used by pymatgen.

"automatic linemode" looks very useful for bandstructure calculations but is 
never used anywhere... I remove it for now. It looks like this is a way to implement
pymatgen.symmetry.bandstructure.HighSymmKpath objects, so I may reimplement this
method when I get there. Alternatively, this method may belond on that class instead.

pymatgen.symmetry.bandstructure.HighSymmKpath objects look to be a great way to
implement kpath setting methods all in one place. I think all DFT calculators
should extend to this module for bandstructures. I want to take this one step
further and say I'll have two generic classes: KptPath and KptGrid that can
be used. For now, KptGrid is just a float value with represent kpt density.

Much like with Poscar, I think Kpoints class should be a converter for a pair of
structures+HighSymmKpath or structure+kpoint_density. That is, you never initialize
the class, but instead you just pass information through it and recieve your
output. See POSCAR notes for more on this. Because of this, it may be useful to
also incorporate a "KptGrid" class that has common methods for us. These
will be used accross all DFT calculators, not just VASP, and it will reduce
repeated code as a result.

see POSCAR notes on from_string, to_string, __str__ methods. Same applies here.

num_kpts, style, kpts, kpts_shift, labels, and kpts_weights are all removed and should
be implemented in the KptGrid and/or KptPath classes.

I didn't take the time to read on what tet_number, tet_weight, and tet_connections
actually do -- but I presume these belong in the KptGrid and/or KptPath
classes as well.

Pymatgen's automatic_density_by_vol actually factors in the number of sites too
so it's really not by volume... Why do they do this? This give density in units
of kpts per atom A^-3. I would think you should choose one or the other.


Ah... It looks like "grid density" they based off of "per atom" which is why
they have all of those conversions. Makes sense. So kppa = kpts per atom.
I still think it makes moresense to have kpt density per volume rather than per
atom. Their method for automatic_density_by_vol is even "per (site * volume)"
which is odd to me. In this case I think you should be able to specify Kpt
density per site OR kpt density per volume -- maybe take the greater/lesser of
the two. Either way, this can be implemented in the KptGrid class. In Simmate,
I'm going to give preference to kpts per volume. Also note, volume here is the
reciprocal space volume!

## POTCAR NOTES

Removed as_dict and from_dict methods for now. Will reimplement later if it's
even needed for this Converter class.

Pymatgen stores all of your vasp potcar files inside of a folder called my_psp
and they save it to the module location. Because of this, I think conda envs
actually get messed up when you try to initialize multiple enviornments for the
potcar files. Instead, I think you should either 1) let the user indicate exactly
where the files are located or 2) have a simmate/ folder in their home directory.
This makes it so users can see exactly where their files are located. I don't
think you should mess with the site-packages folder as this could even cause issues
on shared installs. There should instead be at simmate configuration folder that
is easily accessible.

Vasp provides their POTCARs in a dist/Potentials folder. Pymatgen takes their
format and changes it. I don't think this should be done. Instead I want to keep
their original folder structure and just move it to /simmate/vasp/Potentials
This saves the user from having to rename anything and also saves us from having
to code it and confuse the user where it's being stored

Together, the simmate folder means I can also just copy/paste a configuration
folder to a new computer if I'd like.

I need to learn more about other DFT programs but I'm sure there's a generic
use for a Potential class. Then Potcar class is just a means to 1) copy the 
proper potcar to the correct spot or 2) load data and metadata of the potcar
into a Potential class. Pymatgen loads the entire Potcar data then writes the
file, whereas this loading of data only needs to be done if you want a Potential
object and will look at the data inside it. To write the file, we only need
the potcars location -- nothing else!

The Potential class that I would write would absorb the follow attributes and
settings from this Potcar class: electron_configuration, element, atomic_no,
nelectrons, symbol, potential_type, functional, functional_class

I like how pymatgen hashes the potcar files, but I'm not sure this is needed.
Is file corruption really that common? Also do we need to hash every time the
file is loaded? The strongest argument I can see is to ensure users are providing
POTCARs that are known and not some incorrect file. For now, I remove their
hashing functionality and hash library, but I may add these back in later.

Because hashing functionality was removed, so is the identify_potcar method. The
mapping dictionary in this was very helpful though. I can add this method back
in if I reimplement the hash.

From the map in identify_potcar, it looks like a number of potentials are outdated
and shouldn't be used. Therefore, I don't think Simmate should support them. It
removed clutter for confused users and let's them focus on whats important and
still relevent.
    LDA/
        potpaw_LDA/ >> outdated
        potpaw_LDA.52/ >> supported but not latest version
        potpaw_LDA.54/ >> most current version
        potUSPP_LDA/ >> outdated
    PBE/
        potpaw_PBE/ >> outdated
        potpaw_PBE.52/ >> supported but not latest version
        potpaw_PBE.54/ >> most current version
    PW91/
        potpaw_GGA/ >> outdated
        potUSPP_GGA/ >> outdated
Pymatgen has mappings for unvie_potpaw* potcars as well. I dont see these in
my VASP source files. What are they? 
I think I've been using PBE instead of PBE.54 this entire time... wtf VASP and
pymatgen. How is this not clearly written in documentation somewhere. Even
searching it now I don't see this info. This is why Simmate is going to be
opinionated. Users will be told their using PBE.54 from the start and can change
it if they really want to.

The metadata for the POTCAR (stored in potcar.keywords), should immediately be
mapped to the Potential class keywords for consistency. Some of these I may
need early on (such as ZVAL), so I may create this Potential class before even
looking at other DFT calculators.

In my mappings, I only map to the current versions of LDA and PBE to ensure
users choose the correct POTCARs. I think supporting past versions will only
create a tripping point for new users like it did for me. If an advanced user
really wants to use a older poscar, they can "trick" simmate by renaming their
folder or by writing their own custom class + mappings.

Where should POTCAR_CONFIG go and take effect? I'm thinking that I should not
have a user-set default potential at a low level, but instead have the potential
used always set at the Task level. That way, it's right there for the user to
see and they don't have to dig backwards for inheritance. The other thought is
that the potential type (such as "PAW-GGA-PBE" or "PAW-GGA-PBE-GW") or similar
flags should point straight to the proper POTCAR within the coordination at
the bottom level and completely fixed/opinionated. I'm leaning towards the
latter because I don't think mappings will change often for a given type
and this allows us to just use the "PAW-GGA-PBE" flag at higher levels. This
is what I implement for now.

I still need a better understanding of the different types of Potentials and how
to classify them (e.g. PAW > GGA > PBE). For example, I'm not sure what GW type
potentials are. Are they their own subclass of GGA just like PBE and PBEsol? PBEgw
potentials have their own potentials though, whereas other GGA types of
exchange-correlation like PBEsol you still use PBE's POTCARs and then just 
change a setting in the INCAR settings: https://www.vasp.at/wiki/index.php/GGA

The separation of Potcar and PotcarSingle is removed. There is now only the
Potcar class that handles both types. The key difference is that the input
always takes a list of elements (or list of Potentials). The list gains preference
because more often then not, we are working with >1 element compositions. I
could allow a single input or a list input, but I just force list input for now.

I need to add symbols method to print what functionals would be used. 

I should add a nelectrons method that indicates the normal amount of electrons
used by the potcar. This can be used at a higher level to set NELECT in the Incar
if we want to add/remove charge for doping experiments.

## OTHER NOTES

The final class in pymatgen.io.vasp.inputs is VaspInput. This is moved away
from simmate's io and to setup. Look at simmate.calculators.vasp.stages.setup
for notes on how I modified this class.
