
## SETUP NOTES

Pymatgen has a few classes in order to pull together their inputs and run a
VASP calculation. There's VaspInput in inputs.py and VaspInputSet in sets.py.
VaspInputSet even has a DictSet class that everything runs through and all
of their yaml configurations files are loaded through that. I think is a bit
of a mess and makes it super difficult for programmers to see what's going on.
Sure, writing a yaml is straight forward, but we can do that without all of
these separate classes and inheritance.

VaspInput set is never even used directly. Why do they even separate this class
from DictSet -- which is the only class to inherit from it. Further, the
run_method isn't used either. This is because the class is used strictly for
writing inputs, not running vasp. Atomate delegates that to a shelltask.

from_directory and write_input of VaspInput is really just a wrapper to call
Incar, Poscar, Potcar, and Kpoints classes' from_file methods.

VaspInput has support for optional_files, but I'm not sure when/where this
would be used. Pymatgen, custodian, and atomate have no references for it,
so I just remove this support.

VaspInputSet's potcar_symbols should be be moved to Potcar.symbols. I delete it
from this class.

potcar warnings if the symbol disagrees with the selected functional. I don't
do this check but instead just let the error raise when the symbol is not found
inside the potcar mappings.

all_input can be used to get all of the proper simmate objects back such as
structure, KptGrid, Potential(s), and DftSettings.

get_vasp_input is removed as I merge all of these classes

does the from_directory method make sense for setup class? It's purpose is to
write input files, and I'm not sure it makes sense to load them. There may
be use if we are doing from_previous_calc though.

_load_yaml_config method is removed as I have all configuration in python now

The zip_ouput option is no longer suported at this level. Instead this should
be done at the Task or Workflow level.

calculate_ng is removed for now as I never see it actually used. For bader
calculations, it may be useful to have a FftGrid class that can incorporate
density of the fft grid for us.

DictSet has a number of input options that may be worth including, but I don't
think this is the proper level for them. It should either be a higher or lower
level for these. For example, some of these should be implemented by the input
class and set by the Task. Therefore, this inputset is just an intermediate to
pass along those settings.
    constrain_total_magmom
    sort_structure
    reduce_structure 
    force_gamma 
    vdw 
    use_structure_charge 
    standardize 
    sym_prec 
    international_monoclinic 
    validate_magmom 
    

batch_write_input is removed as parallel functionality is now implemented at a
higher level (task or workflow level)

get_structure_from_prev_run is removed as you should just use Poscar.from_file("CONTCAR")

get_vasprun_outcar is removed as this belongs in workup.

There's a lot of logic for making setting the MAGMOM in this class, but I will
move this to the INCAR class. The same goes for the U parameter and EDIFF_PER_ATOM

Where should I put logic for the type of smearing method?
