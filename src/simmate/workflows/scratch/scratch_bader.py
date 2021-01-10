# -*- coding: utf-8 -*-

from pymatgen.io.vasp.sets import DictSet

#!!! The warning that is raised here is because there is no YAML! It can be ignored
class MyCustomSet(DictSet):

    CONFIG = {'INCAR': {'EDIFF': 1.0e-07,
                        'EDIFFG': -1e-04, 
                        'ENCUT': 500,
                        # 'ISIF': 3, #!!! do I want this..?
                        'ISMEAR': 0, # Guassian smearing #!!! read docs!
                        'LCHARG': True, # write CHGCAR
                        'LAECHG': True, # write AECCAR0, AECCAR1, and AECCAR2
                        'LWAVE': False,
                        'NSW': 0, # single energy calc
                        'PREC': 'Accurate',
                        'SIGMA': 0.05,
                        
                        # set FFT grid and fine FFT grid (note: start with fine!)
                        #!!! YOU SHOULD EXPERIMENT WITH THESE UNTIL THEY CONVERGE THE BADER CHARGES
                        # !!! SHOULD I MESS WITH NGX instead of NGXF???
                        # 'NGX': 100,
                        # 'NGY': 100,
                        # 'NGZ': 100,
                        # If prec = 'Single', then fine grid will automatically match
                        # the NGX,Y,Z above and you don't need to set these.
                        # 'NGXF': 100,
                        # 'NGYF': 100,
                        # 'NGZF': 100,
                        
                        },
              'KPOINTS': {'reciprocal_density': 25},
              'POTCAR_FUNCTIONAL': 'PBE',
              'POTCAR': {'Ac':'Ac','Ag':'Ag','Al':'Al','Ar':'Ar','As':'As',
                         'Au':'Au','B':'B','Ba':'Ba_sv','Be':'Be_sv','Bi':'Bi',
                         'Br':'Br','C':'C','Ca':'Ca_sv','Cd':'Cd','Ce':'Ce',
                         'Cl':'Cl','Co':'Co','Cr':'Cr_pv','Cs':'Cs_sv',
                         'Cu':'Cu_pv','Dy':'Dy_3','Er':'Er_3','Eu':'Eu',
                         'F':'F','Fe':'Fe_pv','Ga':'Ga_d','Gd':'Gd','Ge':'Ge_d',
                         'H':'H','He':'He','Hf':'Hf_pv','Hg':'Hg','Ho':'Ho_3',
                         'I':'I','In':'In_d','Ir':'Ir','K':'K_sv','Kr':'Kr',
                         'La':'La','Li':'Li_sv','Lu':'Lu_3','Mg':'Mg_pv',
                         'Mn':'Mn_pv','Mo':'Mo_pv','N':'N','Na':'Na_pv',
                         'Nb':'Nb_pv','Nd':'Nd_3','Ne':'Ne','Ni':'Ni_pv',
                         'Np':'Np','O':'O','Os':'Os_pv','P':'P','Pa':'Pa',
                         'Pb':'Pb_d','Pd':'Pd','Pm':'Pm_3','Pr':'Pr_3',
                         'Pt':'Pt','Pu':'Pu','Rb':'Rb_sv','Re':'Re_pv',
                         'Rh':'Rh_pv','Ru':'Ru_pv','S':'S','Sb':'Sb','Sc':'Sc_sv',
                         'Se':'Se','Si':'Si','Sm':'Sm_3','Sn':'Sn_d','Sr':'Sr_sv',
                         'Ta':'Ta_pv','Tb':'Tb_3','Tc':'Tc_pv','Te':'Te',
                         'Th':'Th','Ti':'Ti_pv','Tl':'Tl_d','Tm':'Tm_3',
                         'U':'U','V':'V_pv','W':'W_pv','Xe':'Xe','Y':'Y_sv',
                         'Yb':'Yb_2','Zn':'Zn','Zr':'Zr_sv'}
                 }
    
    def __init__(self, structure, **kwargs):
        """
        :param structure: Structure
        :param kwargs: Same as those supported by DictSet.
        """
        super().__init__(structure, MyCustomSet.CONFIG, **kwargs)
        self.kwargs = kwargs

#-----------------------------------------------------------------------------

print('Setting up...')

# load structure
from pymatgen.core.structure import Structure
structure = Structure.from_file('2_POSCAR')
structure = structure.get_primitive_structure()

# write the vasp input files
MyCustomSet(structure).write_input(".")

# run vasp
import subprocess
print('Running vasp...')
subprocess.run('module load vasp; mpirun -np 20 /nas/longleaf/apps-dogwood/vasp/5.4.4/bin/vasp_std > vasp.out', shell=True)

print('Running bader...')
# Download the two executables from...
# http://theory.cm.utexas.edu/henkelman/code/bader/
subprocess.run('./chgsum.pl AECCAR0 AECCAR2 > addingcharges.out', shell=True)
subprocess.run('./bader CHGCAR -ref CHGCAR_sum -b weight  > bader.out', shell=True)
#!!! Play with -vac maybe? "-vac 4E-2" with Ca2N
#!!! Also if I make a custom density file from CHGCAR, use -i chgcar
#!!! What does -cp do?
#!!! In the future I can use...
#!!!    https://pymatgen.org/pymatgen.command_line.bader_caller.html
#!!!    https://wiki.fysik.dtu.dk/gpaw/tutorials/bader/bader.html
# "-b weight" throws some errors in a few cases (there's no refinement step like in the defualt)

print('Done!')

#-----------------------------------------------------------------------------



