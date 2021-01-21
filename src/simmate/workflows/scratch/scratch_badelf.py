# -*- coding: utf-8 -*-

from pymatgen.io.vasp.sets import DictSet

#!!! The warning that is raised here is because there is no YAML! It can be ignored
class MyCustomSet(DictSet):

    CONFIG = {'INCAR': {'EDIFF': 1.0e-07,
                        'EDIFFG': -1e-04, 
                        'ENCUT': 520,
                        'ISIF': 3, #!!! do I want this..?
                        'ISMEAR': 0, # Guassian smearing #!!! read docs!
                        'LCHARG': True, # write CHGCAR
                        'LAECHG': True, # write AECCAR0, AECCAR1, and AECCAR2
                        'LWAVE': False,
                        'NSW': 0, # single energy calc
                        'PREC': 'Single', #!!! Testing: to get ELFCAR grid size to equal CHGCAR. Otherwise use 'Accurate'
                        # 'SIGMA': 0.05, # !!! USING VALUE BELOW FOR TESTING
                        
                        # EXTRA TESTING
                        'IVDW': 12, # van der waals correction
                        'ISMEAR': 0, # Guassian smearing
                        'SIGMA': 0.060,
                        # 'NBANDS': 643, # Calculate more bands than normal (extra empty)
                        
                        
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
                        
                        #!!! TESTING
                        # ELFCAR (optional)
                        'LELF': True, # write ELFCAR
                        'NPAR': 1, # Must be set if LELF is set to True
                        
                        'SYMPREC': 1e-8, #!!! CUSTODIAN FIX - dont use unless needed
                        # 'ISYM': 0,
                        
                        },
              'KPOINTS': {'reciprocal_density': 100},
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

import pandas

def parse_ACF(filename = "ACF.dat"):
    
    # open the file, grab the lines, and then close it
    file = open(filename)
    lines = file.readlines()
    file.close()
    
    # establish the headers. Note that I ignore the '#' column as this is just site index.
    headers = ("x", "y", "z", "charge", "min_dist", "atomic_vol")
    
    # create a list that we will load data into
    bader_data = []
    # The first 2 lines are header and the final 4 lines are the footer. This is always
    # true so we don't need to iterate through those. The data we want is between the 
    # header and footer so that's what we loop through.
    for line in lines[2:-4]:
        # by running strip, we convert the line from a string to a list of 
        # The values are all still strings, so we convert them to int/floats before saving
        # I add [1:] because the first value is just '#' which is site index and we dont need
        line_data = [eval(value) for value in line.split()[1:]]
        # add the line data to our ouput
        bader_data.append(line_data)
    
    # convert the list to a pandas dataframe
    dataframe = pandas.DataFrame(
        data = bader_data,
        columns = headers,
        )
    
    # Extra data is included in the footer that we can grab too. For each line, the data
    # is a float that is at the end of the line, hence the split()[-1].
    extra_data = {
        "vacuum_charge": float(lines[-3].split()[-1]),
        "vacuum_volume": float(lines[-2].split()[-1]),
        "nelectrons": float(lines[-1].split()[-1]),
        }
    
    return dataframe, extra_data

    # This is how pymatgen parses the ACF.dat file
    # data = []
    # with open("ACF.dat") as f:
    #     raw = f.readlines()
    #     headers = ("x", "y", "z", "charge", "min_dist", "atomic_vol")
    #     raw.pop(0)
    #     raw.pop(0)
    #     while True:
    #         l = raw.pop(0).strip()
    #         if l.startswith("-"):
    #             break
    #         vals = map(float, l.split()[1:])
    #         data.append(dict(zip(headers, vals)))
    #     for l in raw:
    #         toks = l.strip().split(":")
    #         if toks[0] == "VACUUM CHARGE":
    #             vacuum_charge = float(toks[1])
    #         elif toks[0] == "VACUUM VOLUME":
    #             vacuum_volume = float(toks[1])
    #         elif toks[0] == "NUMBER OF ELECTRONS":
    #             nelectrons = float(toks[1])

# -----------------------------------------------------------------------------

from pymatgen.io.vasp import Potcar

def get_nelectron_counts(filename='POTCAR'):
    # Grabbing the number of electrons used by the POTCAR
    #!!! In the future, I can have a reference csv that would be much faster than parsing
    #!!! the entire POTCAR file just for this one piece of information.
    potcars = Potcar.from_file(filename)
    
    nelectron_data = {}
    # the result is a list because there can be multiple element potcars in the file 
    for potcar in potcars:
        nelectron_data.update({potcar.element: potcar.nelectrons})
    
    return nelectron_data

# -----------------------------------------------------------------------------

print('Setting up...')

# load structure
from pymatgen.core.structure import Structure
structure = Structure.from_file('Y2C.cif') ###################################################
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
# subprocess.run('./bader CHGCAR -ref CHGCAR_sum -b weight  > bader.out', shell=True)
#!!! Play with -vac maybe? "-vac 4E-2" with Ca2N
#!!! Also if I make a custom density file from CHGCAR, use -i chgcar
#!!! What does -cp do?
#!!! In the future I can use...
#!!!    https://pymatgen.org/pymatgen.command_line.bader_caller.html
#!!!    https://wiki.fysik.dtu.dk/gpaw/tutorials/bader/bader.html
# "-b weight" throws some errors in a few cases (there's no refinement step like in the defualt)

# -----------------------------------------------------------------------------

# Load ELFCAR and add "empty" atom (I use Hydrogen)
from pymatgen.io.vasp.outputs import Elfcar
elfcar = Elfcar.from_file('ELFCAR')
structure = elfcar.structure
structure.append('H', [0.5,0.5,0.5])
elfcar.write_file('ELFCAR_empty')

# also write the crystal structure because it may differ from the input
elfcar.structure.to(filename='primitive_structure_empty.cif')

# Load CHGCAR (valence e- only) and add "empty" atom (I use Hydrogen)
from pymatgen.io.vasp.outputs import Chgcar
chgcar = Chgcar.from_file('CHGCAR')
structure = chgcar.structure
structure.append('H', [0.5,0.5,0.5])
chgcar.write_file('CHGCAR_empty')

# Run bader analysis with ELFCAR_empty as the reference file
subprocess.run('./bader CHGCAR_empty -ref ELFCAR_empty > bader.out', shell=True)

# -----------------------------------------------------------------------------

# from pymatgen.core.structure import Structure
# structure = Structure.from_file("1_POSCAR")

# # for M2NX (M=Sr,Ca; X=Cl,F,e) and Y2CX2 (X=Cl,F,e) bulk structures
# # structure.append('H', [0.5,0.5,0.5])

# # # M2NX (M=Sr,Ca; X=F,Cl) - divacancy
# # structure.append('H', [0.6666,0.6666,0.5])
# # structure.append('H', [0.3333,0.3333,0.5])
# # # structure.append('H', [0.6666,0.3333,0.5]) # 1_POSCAR only

# # Ca2NF and Sr2NCl/F - o-o
# #!!! Did she not give me the midpoint...?
# # structure.append('H', [0.3333,0.3333,0.5])  # 1_POSCAR only, 'SYMPREC': 1e-8 for Ca2NF
# # structure.append('H', [0.6666,0.6666,0.5]) # 2_POSCAR only

# # # Ca2NCl - o-o
# # #!!! Did she not give me the midpoint...?
# # structure.append('H', [0.6666,0.3333,0.5])  # 1_POSCAR only
# # # structure.append('H', [0.6666,0.6666,0.5]) # 2_POSCAR only

# # Y2CF2 - t1-t1
# #!!! Did she not give me the midpoint...?
# # structure.append('H', [0.55555, 0.44444, 0.53770])  # 1_POSCAR only
# # structure.append('H', [0.55555, 0.77778, 0.53770])  # 2_POSCAR only
# structure.append('H', [0.55555, 0.44444, 0.55555])  #!!! TEST MOVING 1_POSCAR UP

# # # Y2CF2 - t1-t2
# # # structure.append('H', [0.44444, 0.55556, 0.46230])  # 1_POSCAR only
# # structure.append('H', [0.55555, 0.44444, 0.53770])  # 2_POSCAR only

# # # Y2CCl2 - t1-t1
# # #!!! Did she not give me the midpoint...?
# # structure.append('H', [0.55555, 0.44444, 0.56129])  # 1_POSCAR only 'SYMPREC': 1e-8 for Ca2NF
# # # structure.append('H', [0.55555, 0.77778, 0.56129])  # 2_POSCAR only

# # line if I want to view file
# structure.to(filename='POSCAR_empty.vasp')

# Ca2NF
# bulk_ref = {
#     "Ca": 1.678,
#     "N": -2.415,
#     "F": -0.941,
#     "H": 0,
#     }

# Ca2NCl
# bulk_ref = {
#     "Ca": 1.693,
#     "N": -2.434,
#     "Cl": -0.951,
#     "H": 0,
#     }

# # Sr2NCl
# bulk_ref = {
#     "Sr": 1.692,
#     "N": -2.439,
#     "Cl": -0.946,
#     "H": 0,
#     }

# # Sr2NF
# bulk_ref = {
#     "Sr": 1.680,
#     "N": -2.426,
#     "F": -0.935,
#     "H": 0,
#     }

# # Y2CF2
# bulk_ref = {
#     "Y": 2.386,
#     "C": -3.035,
#     "F": -0.868,
#     "H": 0,
#     }

# # Y2CCl2
# bulk_ref = {
#     "Y": 2.374,
#     "C": -3.006,
#     "Cl": -0.871,
#     "H": 0,
#     }

# -----------------------------------------------------------------------------

# # After bader is ran, we want to look at the data
# dataframe, extra_data = parse_ACF(filename = "ACF.dat")
# nelectron_data = get_nelectron_counts()
# nelectron_data.update({'H': 0}) # I need to add this for the empty atoms

# # reload the structure used if I don't have it already
# from pymatgen.io.vasp.outputs import Elfcar
# elfcar = Elfcar.from_file('ELFCAR_empty')

# # Calculate the oxidation state of each site where it is simply the change in number of
# # electrons associated with it (from vasp potcar vs the bader charge)
# # I also add the element strings for filtering functionality
# elements = []
# oxi_state_data = []
# for site, site_charge in zip(elfcar.structure, dataframe.charge.values):
#     element_str = site.specie.name
#     elements.append(element_str)
#     oxi_state = nelectron_data[element_str] - site_charge
#     oxi_state_data.append(oxi_state)
# # add the new column to the dataframe
# #!!! There are multiple ways to do this, but I don't know which is best
# # dataframe["oxidation_state"] = pandas.Series(oxi_state_data, index=dataframe.index)
# dataframe = dataframe.assign(
#     oxidation_state = oxi_state_data,
#     element = elements
#     )

# # look at the median, max and min, for each element
# for element_str in nelectron_data.keys():
#     data_filtered = dataframe[dataframe.element == element_str]
#     oxi_states = data_filtered.oxidation_state
#     print("Summary for", element_str, "...")
#     print("Median:", oxi_states.median())
#     print("Max:", oxi_states.max())
#     print("Max:", oxi_states.min())
    
#     # output for my reference
#     # Format of dMedian (dMin to dMax)
#     print(oxi_states.median() - bulk_ref[element_str], 
#           oxi_states.max() - bulk_ref[element_str],
#           oxi_states.min() - bulk_ref[element_str],
#           )
    
#     print('\n')

# print('Done!')

# testing
# raise MemoryError

# -----------------------------------------------------------------------------
