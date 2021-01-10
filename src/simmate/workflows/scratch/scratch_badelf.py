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
                        'PREC': 'Single', #!!! Testing: to get ELFCAR grid size to equal CHGCAR. Otherwise use 'Accurate'
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
                        
                        #!!! TESTING
                        # ELFCAR (optional)
                        'LELF': True, # write ELFCAR
                        'NPAR': 1, # Must be set if LELF is set to True
                        
                        # 'SYMPREC': 1e-8, #!!! CUSTODIAN FIX - dont use unless needed
                        
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

#-----------------------------------------------------------------------------

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

#-----------------------------------------------------------------------------

print('Setting up...')

# load structure
from pymatgen.core.structure import Structure
structure = Structure.from_file('1_POSCAR') ###################################################
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

#-----------------------------------------------------------------------------

# Load ELFCAR and add "empty" atom (I use Hydrogen)
from pymatgen.io.vasp.outputs import Elfcar
elfcar = Elfcar.from_file('ELFCAR')
structure = elfcar.structure
structure.append('H', [0.55555, 0.44444, 0.55555])  #!!! TEST MOVING 1_POSCAR UP
elfcar.write_file('ELFCAR_empty')

# also write the crystal structure because it may differ from the input
# elfcar.structure.to(filename='primitive_structure_empty.cif')

# Load CHGCAR (valence e- only) and add "empty" atom (I use Hydrogen)
from pymatgen.io.vasp.outputs import Chgcar
chgcar = Chgcar.from_file('CHGCAR')
structure = chgcar.structure
structure.append('H', [0.55555, 0.44444, 0.55555])  #!!! TEST MOVING 1_POSCAR UP
chgcar.write_file('CHGCAR_empty')

# Run bader analysis with ELFCAR_empty as the reference file
subprocess.run('./bader CHGCAR_empty -ref ELFCAR_empty > bader.out', shell=True)

#-----------------------------------------------------------------------------

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

# Y2CF2
bulk_ref = {
    "Y": 2.386,
    "C": -3.035,
    "F": -0.868,
    "H": 0,
    }

# # Y2CCl2
# bulk_ref = {
#     "Y": 2.374,
#     "C": -3.006,
#     "Cl": -0.871,
#     "H": 0,
#     }

#-----------------------------------------------------------------------------

# After bader is ran, we want to look at the data
dataframe, extra_data = parse_ACF(filename = "ACF.dat")
nelectron_data = get_nelectron_counts()
nelectron_data.update({'H': 0}) # I need to add this for the empty atoms

# reload the structure used if I don't have it already
from pymatgen.io.vasp.outputs import Elfcar
elfcar = Elfcar.from_file('ELFCAR_empty')

# Calculate the oxidation state of each site where it is simply the change in number of
# electrons associated with it (from vasp potcar vs the bader charge)
# I also add the element strings for filtering functionality
elements = []
oxi_state_data = []
for site, site_charge in zip(elfcar.structure, dataframe.charge.values):
    element_str = site.specie.name
    elements.append(element_str)
    oxi_state = nelectron_data[element_str] - site_charge
    oxi_state_data.append(oxi_state)
# add the new column to the dataframe
#!!! There are multiple ways to do this, but I don't know which is best
# dataframe["oxidation_state"] = pandas.Series(oxi_state_data, index=dataframe.index)
dataframe = dataframe.assign(
    oxidation_state = oxi_state_data,
    element = elements
    )

# look at the median, max and min, for each element
for element_str in nelectron_data.keys():
    data_filtered = dataframe[dataframe.element == element_str]
    oxi_states = data_filtered.oxidation_state
    print("Summary for", element_str, "...")
    print("Median:", oxi_states.median())
    print("Max:", oxi_states.max())
    print("Max:", oxi_states.min())
    
    # output for my reference
    # Format of dMedian (dMin to dMax)
    print(oxi_states.median() - bulk_ref[element_str], 
          oxi_states.max() - bulk_ref[element_str],
          oxi_states.min() - bulk_ref[element_str],
          )
    
    print('\n')

# testing
raise MemoryError

#-----------------------------------------------------------------------------

"""
While this works, the scientific argument for it is much weaker. It's best to just use
the ELFCAR as the reference file in bader analysis
"""

# TESTING -- Multiplying ELFCAR by CHGCAR or CHGCAR_sum

# Load CHGCAR_sum (valence and core electrons) and add "empty" atom (I use Hydrogen)
# chgcar_sum = Chgcar.from_file('CHGCAR_sum')
# structure = chgcar_sum.structure
# structure.append('H', [0.5,0.5,0.5])
# chgcar_sum.write_file('CHGCAR_sum_empty') #!!! Bug -- data_aug should be {}

#!!! NOTE: ELFCAR and CHGCAR voxel data must have the same dimensions (NGX - )
# test = elfcar.data["total"] * chgcar.data["total"]
# test = Elfcar(elfcar.structure, {"total": test})
# test.write_file('TESTCAR')

# subprocess.run('./bader CHGCAR -ref TESTCAR -b weight  > bader.out', shell=True)

#-----------------------------------------------------------------------------

"""
Based on my testing in this section, scaling the ELFCAR to match the CHGCAR dimensions
fails because we really have a step function in the scaled ELFCAR. I can get it to work
by smoothing (guassian) the scaled ELFCAR, but I show that the choice of sigma does 
affect the resultant oxidation states. Therefore, I can't use this approach.
Instead, I need to set the FFT grid and fine grid to be the same size in VASP.
"""

# # TESTING -- I loop through different smoothing amounts for the ELFCAR data

# def get_empty_charge(): #!!! I ASSUME 4 ATOMS TOTAL -- for Y2C testings
#     # grab the vacuum charge
#     file = open('ACF.dat', 'r')
#     lines = file.readlines()
#     # grab line 6
#     line = lines[5] # 5, 4, 3
#     # grab the proper column data
#     charge = float(line.split(' ')[17]) # 17, 20, 17
#     file.close()
#     return charge

# scale data of the Elfcar to the size of Chgcar using Kronecker product
# The voxel data is not smoothed in any way, so we now have a step function.
# I smooth below
# import numpy as np
# scale = [int(c/e) for c,e in zip(chgcar.data["total"].shape, elfcar.data["total"].shape)]
# elfcar_scaled = np.kron(elfcar.data["total"], np.ones(scale))
# 
# x = np.linspace(0.5, 10, 100)
# y = []

# for sigma in x:
#     # Smooth the voxel data
#     from scipy.ndimage import gaussian_filter
#     elfcar_smoothed_data = gaussian_filter(elfcar_scaled, sigma=sigma)
    
#     # Write the scaled&smoothed ELFCAR to file
#     elfcar_smoothed = Elfcar(elfcar.structure, {"total": elfcar_smoothed_data})
#     elfcar_smoothed.write_file('ELFCAR_smoothed')
    
#     # run the bader analysis using the new ELFCAR as the reference
#     subprocess.run('./bader CHGCAR_empty -ref ELFCAR_smoothed -b weight > bader.out', shell=True)
    
#     try:
#         vac_charge = get_empty_charge()
#         y.append(vac_charge)
#     except:
#         y.append(None)
    
# print(y)
# # e
# y = [None, 0.992909, 0.992209, 0.991662, 0.991145, 0.990615, 0.990056, 0.990056, 0.98884, 0.988193, 0.988193, 0.98684, 0.98684, 0.985466, 0.984788, 0.984121, 0.984121, 0.982851, 0.982256, 0.981693, 0.981166, 0.980678, 0.980678, 0.980678, 0.980678, 0.979172, 0.978921, 0.978921, 0.978587, 0.978506, 0.97849, 0.978538, 0.978654, 0.978846, 0.979111, 0.979455, 0.979881, 0.980391, 0.980989, 0.981675, 0.982453, 0.983326, 0.984301, 0.985378, 0.986561, 0.987843, 0.989227, 0.990721, 0.992327, 0.994039, 0.995872, 0.997807, 0.999858, 1.002025, 1.004306, 1.006713, 1.009225, 1.011838, 1.014584, 1.017437, 1.020383, 1.02341, 1.026532, 1.029778, 1.033074, 1.036418, 1.039802, 1.043235, 1.046726, 1.050228, 1.053718, 1.057219, 1.060725, 1.064251, 1.067752, 1.071207, 1.074643, 1.078045, 1.081421, 1.084752, 1.088011, 1.091212, 1.094343, 1.097396, 1.10038, 1.103292, 1.106136, 1.108919, 1.111637, 1.114291, 1.116888, 1.119428, 1.121915, 1.124353, 1.126744, 1.129091, 1.131402, 1.133656, 1.135881, 1.138057]
# # C
# y = [None, 7.396851, 7.395889, 7.394598, 7.39312, 7.391522, 7.38985, 7.38985, 7.386323, 7.384511, 7.384511, 7.380842, 7.380842, 7.377237, 7.375487, 7.373776, 7.373776, 7.370608, 7.369179, 7.367864, 7.36668, 7.365641, 7.365641, 7.365641, 7.365641, 7.362932, 7.362617, 7.362617, 7.362477, 7.362658, 7.362997, 7.363492, 7.364137, 7.364923, 7.365858, 7.366935, 7.368155, 7.369517, 7.37101, 7.37262, 7.374327, 7.376119, 7.377964, 7.379852, 7.381786, 7.383743, 7.385726, 7.387721, 7.389733, 7.391748, 7.393759, 7.395763, 7.397751, 7.399697, 7.401578, 7.403364, 7.405066, 7.406717, 7.408297, 7.409819, 7.411305, 7.412722, 7.414123, 7.415479, 7.416784, 7.418011, 7.419202, 7.420367, 7.421503, 7.422647, 7.423685, 7.424675, 7.425707, 7.426722, 7.427743, 7.428884, 7.430021, 7.431037, 7.432156, 7.433463, 7.434781, 7.435971, 7.437295, 7.438744, 7.440297, 7.441632, 7.443059, 7.444757, 7.446546, 7.449092, 7.450574, 7.452824, 7.460178, 7.463841, 7.468499, 7.473979, 7.479626, 7.487133, 7.49945, 7.517937]
# # Y
# y = [None, 8.287864, 8.288695, 8.289602, 8.290587, 8.291641, 8.292744, 8.292744, 8.295078, 8.296275, 8.296275, 8.29868, 8.29868, 8.300985, 8.302075, 8.30312, 8.30312, 8.305012, 8.305842, 8.306589, 8.307241, 8.307784, 8.307784, 8.307784, 8.307784, 8.30888, 8.308888, 8.308888, 8.308537, 8.308181, 8.307703, 8.307111, 8.306407, 8.305589, 8.304658, 8.303622, 8.302479, 8.301235, 8.299892, 8.298456, 8.296938, 8.295343, 8.293688, 8.291978, 8.29021, 8.288392, 8.286534, 8.284634, 8.282679, 8.280676, 8.278635, 8.276564, 8.274455, 8.272311, 8.270145, 8.267981, 8.26583, 8.263642, 8.261414, 8.259126, 8.256784, 8.25443, 8.25205, 8.249604, 8.24715, 8.244716, 8.242264, 8.239781, 8.237296, 8.234788, 8.232305, 8.229801, 8.227243, 8.224628, 8.221934, 8.219171, 8.216279, 8.213283, 8.210157, 8.206906, 8.203531, 8.199971, 8.196206, 8.19227, 8.188098, 8.183801, 8.179244, 8.17438, 8.169046, 8.16299, 8.157541, 8.150598, 8.139021, 8.130364, 8.120871, 8.110239, 8.098494, 8.084827, 8.066644, 8.041329]

#-----------------------------------------------------------------------------

"""
I was exploring a way to identify the electride charge here, but decided it wasn't worth
pursuing anymore. 
"""

# # TESTING -- I loop through different vac values here
# import numpy as np
# x = np.linspace(1E-3, 1E-1, 100)
# y = []
# for vac_cutoff in x:
#     # run bader with this cutoff
#     subprocess.run(f'./bader CHGCAR -ref CHGCAR_sum -b weight -vac {vac_cutoff} > bader.out', shell=True)
    
#     # grab the vacuum charge
#     file = open('ACF.dat', 'r')
#     lines = file.readlines()
#     for line in lines:
#         if 'VACUUM CHARGE' in line:
#             vac_charge = float(line.split(' ')[-1])
#     file.close()
#     y.append(vac_charge)

# print(y)
# # y = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0008, 0.0095, 0.0232, 0.0422, 0.0681, 0.1051, 0.164, 0.2886, 0.5189, 0.714, 0.7935, 0.8418, 0.8795, 0.9117, 0.9408, 0.9676, 0.9924, 1.0159, 1.0389, 1.0603, 1.0815, 1.1019, 1.1221, 1.1416, 1.161, 1.1798, 1.1993, 1.2172, 1.236, 1.2539, 1.2721, 1.2895, 1.3074, 1.3249, 1.3426, 1.3602, 1.377, 1.3944, 1.4119, 1.4287, 1.4458, 1.4631, 1.4806, 1.497, 1.5143, 1.5318, 1.549, 1.5662, 1.5825, 1.6007, 1.6185, 1.6361, 1.6531, 1.6709, 1.6893, 1.7089, 1.7282, 1.7466, 1.7648, 1.783, 1.8014, 1.8193, 1.8376, 1.8555, 1.8737, 1.8911, 1.9084, 1.9258, 1.9429, 1.9604, 1.9778, 1.9951]

#-----------------------------------------------------------------------------

# import matplotlib.pyplot as plt
# plt.plot(x,y)

# # take first derivative
# der = (np.diff(y) / np.diff(x)) /200 # divide by 200 for scaling
# x2 = (x[:-1] + x[1:]) / 2
# plt.plot(x2, der, 'r', x, y, 'b')

print('Done!')

#-----------------------------------------------------------------------------



