# -*- coding: utf-8 -*-

from pymatgen.io.vasp.sets import DictSet

#!!! The warning that is raised here is because there is no YAML! It can be ignored
class StaticEnergyCalc(DictSet):

    CONFIG = {
        "INCAR": {
            "EDIFF": 1.0e-07,
            "EDIFFG": -1e-04,
            "ENCUT": 520,
            "ISIF": 3,  # !!! do I want this..?
            "ISMEAR": 0,  # Guassian smearing #!!! read docs!
            # "LCHARG": True,  # write CHGCAR
            "LAECHG": True,  # write AECCAR0, AECCAR1, and AECCAR2
            # "LWAVE": True,
            "NSW": 0,  # single energy calc
            "PREC": "Accurate",
            "IVDW": 12,  # van der waals correction
            "ISMEAR": 0,  # Guassian smearing
            "SIGMA": 0.060,
            # 'NBANDS': 643, # Calculate more bands than normal (extra empty)
            "SYMPREC": 1e-8,  #!!! CUSTODIAN FIX - dont use unless needed
            'ISYM': 0,
        },
        "KPOINTS": {"reciprocal_density": 100},
        "POTCAR_FUNCTIONAL": "PBE",
        "POTCAR": {
            "Ac": "Ac",
            "Ag": "Ag",
            "Al": "Al",
            "Ar": "Ar",
            "As": "As",
            "Au": "Au",
            "B": "B",
            "Ba": "Ba_sv",
            "Be": "Be_sv",
            "Bi": "Bi",
            "Br": "Br",
            "C": "C",
            "Ca": "Ca_sv",
            "Cd": "Cd",
            "Ce": "Ce",
            "Cl": "Cl",
            "Co": "Co",
            "Cr": "Cr_pv",
            "Cs": "Cs_sv",
            "Cu": "Cu_pv",
            "Dy": "Dy_3",
            "Er": "Er_3",
            "Eu": "Eu",
            "F": "F",
            "Fe": "Fe_pv",
            "Ga": "Ga_d",
            "Gd": "Gd",
            "Ge": "Ge_d",
            "H": "H",
            "He": "He",
            "Hf": "Hf_pv",
            "Hg": "Hg",
            "Ho": "Ho_3",
            "I": "I",
            "In": "In_d",
            "Ir": "Ir",
            "K": "K_sv",
            "Kr": "Kr",
            "La": "La",
            "Li": "Li_sv",
            "Lu": "Lu_3",
            "Mg": "Mg_pv",
            "Mn": "Mn_pv",
            "Mo": "Mo_pv",
            "N": "N",
            "Na": "Na_pv",
            "Nb": "Nb_pv",
            "Nd": "Nd_3",
            "Ne": "Ne",
            "Ni": "Ni_pv",
            "Np": "Np",
            "O": "O",
            "Os": "Os_pv",
            "P": "P",
            "Pa": "Pa",
            "Pb": "Pb_d",
            "Pd": "Pd",
            "Pm": "Pm_3",
            "Pr": "Pr_3",
            "Pt": "Pt",
            "Pu": "Pu",
            "Rb": "Rb_sv",
            "Re": "Re_pv",
            "Rh": "Rh_pv",
            "Ru": "Ru_pv",
            "S": "S",
            "Sb": "Sb",
            "Sc": "Sc_sv",
            "Se": "Se",
            "Si": "Si",
            "Sm": "Sm_3",
            "Sn": "Sn_d",
            "Sr": "Sr_sv",
            "Ta": "Ta_pv",
            "Tb": "Tb_3",
            "Tc": "Tc_pv",
            "Te": "Te",
            "Th": "Th",
            "Ti": "Ti_pv",
            "Tl": "Tl_d",
            "Tm": "Tm_3",
            "U": "U",
            "V": "V_pv",
            "W": "W_pv",
            "Xe": "Xe",
            "Y": "Y_sv",
            "Yb": "Yb_2",
            "Zn": "Zn",
            "Zr": "Zr_sv",
        },
    }

    def __init__(self, structure, **kwargs):
        """
        :param structure: Structure
        :param kwargs: Same as those supported by DictSet.
        """
        super().__init__(structure, StaticEnergyCalc.CONFIG, **kwargs)
        self.kwargs = kwargs


class NonSCFCalc(DictSet):

    CONFIG = {
        "INCAR": {
            # "EDIFF": 1.0e-07,
            # "EDIFFG": -1e-04,
            # "ENCUT": 520,
            # "ISIF": 3,  # !!! do I want this..?
            # "ISMEAR": 0,  # Guassian smearing #!!! read docs!
            # # "LCHARG": True,  # write CHGCAR
            # # "LAECHG": True,  # write AECCAR0, AECCAR1, and AECCAR2
            # # "LWAVE": True,
            # "NSW": 0,  # single energy calc
            # "PREC": "Accurate",
            # "IVDW": 12,  # van der waals correction
            # "ISMEAR": 0,  # Guassian smearing
            # "SIGMA": 0.060,
            # # 'NBANDS': 643, # Calculate more bands than normal (extra empty)
            "SYMPREC": 1e-8,  #!!! CUSTODIAN FIX - dont use unless needed
            'ISYM': 0,
            
            # # PDOS
            # "LORBIT": 11,
            # "ICHARG": 11,
            
            # For band-decomposed charge densities
            "LPARD": True, # Yes to doing band-decomposed charge densities
            "LSEPB": True, # whether to combine all bands to one file or separate
            "NBMOD": -3, # calculated partial charge density for only energys specified by EINT (sets EINT to vs Fermi Energy too)
            # "IBAND": ' '.join([str(n) for n in range(1,100)]),
            "EINT": "-9999 0", # energy range to look at for decomposed charge density
            "ISYM": 0,  # turn off symmetry
            # "NBANDS": 50,
            "LSEPK": True, # whether to combine all k-points to one file or separate
        },
        "KPOINTS": {"reciprocal_density": 100},
        "POTCAR_FUNCTIONAL": "PBE",
        "POTCAR": {
            "Ac": "Ac",
            "Ag": "Ag",
            "Al": "Al",
            "Ar": "Ar",
            "As": "As",
            "Au": "Au",
            "B": "B",
            "Ba": "Ba_sv",
            "Be": "Be_sv",
            "Bi": "Bi",
            "Br": "Br",
            "C": "C",
            "Ca": "Ca_sv",
            "Cd": "Cd",
            "Ce": "Ce",
            "Cl": "Cl",
            "Co": "Co",
            "Cr": "Cr_pv",
            "Cs": "Cs_sv",
            "Cu": "Cu_pv",
            "Dy": "Dy_3",
            "Er": "Er_3",
            "Eu": "Eu",
            "F": "F",
            "Fe": "Fe_pv",
            "Ga": "Ga_d",
            "Gd": "Gd",
            "Ge": "Ge_d",
            "H": "H",
            "He": "He",
            "Hf": "Hf_pv",
            "Hg": "Hg",
            "Ho": "Ho_3",
            "I": "I",
            "In": "In_d",
            "Ir": "Ir",
            "K": "K_sv",
            "Kr": "Kr",
            "La": "La",
            "Li": "Li_sv",
            "Lu": "Lu_3",
            "Mg": "Mg_pv",
            "Mn": "Mn_pv",
            "Mo": "Mo_pv",
            "N": "N",
            "Na": "Na_pv",
            "Nb": "Nb_pv",
            "Nd": "Nd_3",
            "Ne": "Ne",
            "Ni": "Ni_pv",
            "Np": "Np",
            "O": "O",
            "Os": "Os_pv",
            "P": "P",
            "Pa": "Pa",
            "Pb": "Pb_d",
            "Pd": "Pd",
            "Pm": "Pm_3",
            "Pr": "Pr_3",
            "Pt": "Pt",
            "Pu": "Pu",
            "Rb": "Rb_sv",
            "Re": "Re_pv",
            "Rh": "Rh_pv",
            "Ru": "Ru_pv",
            "S": "S",
            "Sb": "Sb",
            "Sc": "Sc_sv",
            "Se": "Se",
            "Si": "Si",
            "Sm": "Sm_3",
            "Sn": "Sn_d",
            "Sr": "Sr_sv",
            "Ta": "Ta_pv",
            "Tb": "Tb_3",
            "Tc": "Tc_pv",
            "Te": "Te",
            "Th": "Th",
            "Ti": "Ti_pv",
            "Tl": "Tl_d",
            "Tm": "Tm_3",
            "U": "U",
            "V": "V_pv",
            "W": "W_pv",
            "Xe": "Xe",
            "Y": "Y_sv",
            "Yb": "Yb_2",
            "Zn": "Zn",
            "Zr": "Zr_sv",
        },
    }

    def __init__(self, structure, **kwargs):
        """
        :param structure: Structure
        :param kwargs: Same as those supported by DictSet.
        """
        super().__init__(structure, NonSCFCalc.CONFIG, **kwargs)
        self.kwargs = kwargs


# -----------------------------------------------------------------------------

# if this is the starting point...
from pymatgen.core.structure import Structure

structure = Structure.from_file("Y2C.cif")
structure = structure.get_primitive_structure()
calc = StaticEnergyCalc(structure)

# save the calc files
calc.write_input(".")

# -----------------------------------------------------------------------------

# Now run this calculation

print("Running vasp...")

# run vasp
import subprocess

subprocess.run(
    "module load vasp; mpirun -np 20 /nas/longleaf/apps-dogwood/vasp/5.4.4/bin/vasp_std > vasp.out",
    shell=True,
)

subprocess.run(
    "cp CHG CHG_step1",
    shell=True,
)
subprocess.run('./chgsum.pl AECCAR0 AECCAR2 > addingcharges.out', shell=True)

# -----------------------------------------------------------------------------

structure = Structure.from_file("CONTCAR")
calc = NonSCFCalc(structure)

# save the calc files
calc.write_input(".")

# -----------------------------------------------------------------------------

# Now run this calculation

print("Running vasp...")

# run vasp
import subprocess

subprocess.run(
    "module load vasp; mpirun -np 20 /nas/longleaf/apps-dogwood/vasp/5.4.4/bin/vasp_std > vasp.out",
    shell=True,
)

# -----------------------------------------------------------------------------

# from pymatgen.io.vasp.outputs import Vasprun

# xmlReader = Vasprun(
#     filename="vasprun.xml",
#     parse_dos=True,
#     parse_eigen=True,
#     parse_projected_eigen=True,  #!!! **Note that this can take an extreme amount of time and memory.** So use this wisely.
#     parse_potcar_file=True,
#     exception_on_bad_xml=True,
# )

# # update the structure (really this should be the same)
# structure = xmlReader.structures[0]

# # grab both the total density of states and all the partial densitry of states
# complete_dos = xmlReader.complete_dos

# # now we want to plot the DOS
# from pymatgen.electronic_structure.plotter import DosPlotter

# ########## PLOT 1

# plotter = DosPlotter(
#     zero_at_efermi=True, stack=False, sigma=0.05
# )  #!!! set to None if you dont want smoothing

# # plot the total DOS first
# plotter.add_dos("Total DOS", complete_dos)


# # now lets get the pDOS
# pdos = complete_dos.get_element_dos()
# for element in structure.composition:
#     # grab the single element pdos
#     element_pdos = pdos[element]
#     # add it to the plot
#     plotter.add_dos(element.symbol, element_pdos)

# plot = plotter.get_plot()
# plot.save('test.png')
# # plotter.get_plot(xlim=[-4.5,4.5], ylim=[-0.25,100])

# ########## PLOT 2

# # alternatively I can plot by site
# # I start by resetting the plot

# from scipy.integrate import trapz

# plotter = DosPlotter(
#     zero_at_efermi=True, stack=False, sigma=0.05
# )  #!!! set to None if you dont want smoothing

# # plot the total DOS first
# plotter.add_dos("Total DOS", complete_dos)

# for i, site in enumerate(structure):
#     # grab the single element pdos
#     site_pdos = complete_dos.get_site_dos(site)
#     # add it to the plot
#     plotter.add_dos(i, site_pdos)

#     # INTEGRATE
#     den = site_pdos.densities  # .get_smeared_densities(0.05)
#     den = [den[key] for key in den.keys()]
#     den = den[0]  # + den[1] #!!! with y2c only
#     eng = site_pdos.energies - site_pdos.efermi

#     # INTEGRATE
#     area = trapz(y=den[:1677], x=eng[:1677])

#     symbol = site.specie.symbol
#     if symbol == "F":
#         print(site.specie.symbol + ": " + str(7 - area))
#     elif symbol == "C":
#         print(site.specie.symbol + ": " + str(4 - area))
#     if symbol == "Y":
#         print(site.specie.symbol + ": " + str(11 - area))
#         # print(site.frac_coords)

# plotter.get_plot(xlim=[-5, 5], ylim=[-0.25, 5])

# ########## PLOT 3

# # alternatively I can plot the sum of spins up/down

# # for this, I can't use the pymatgen plotter function

# import matplotlib.pyplot as plt
# from scipy.integrate import trapz  #!!! this isn't giving me accurate integrations

# # from numpy import trapz

# # Create a new figure of size 8x6 points, using 100 dots per inch
# plt.figure(figsize=(10, 6), dpi=80)

# # Create a new subplot from a grid of 1x1
# plt.subplot(111)

# pdos = complete_dos.get_element_dos()
# for element in structure.composition:
#     # grab the single element pdos
#     element_pdos = pdos[element]
#     # add it to the plot
#     den = element_pdos.densities  # .get_smeared_densities(0.05)
#     den = [den[key] for key in den.keys()]
#     den = den[0]  # + den[1] #!!! with y2c only
#     eng = element_pdos.energies - element_pdos.efermi

#     # INTEGRATE
#     area = trapz(y=den[:1677], x=eng[:1677])  # 1263
#     print(element.symbol + ": " + str(area))

#     plt.plot(eng, den, label=element.symbol, linewidth=2.5, linestyle="-")

# plt.xlim(-4.0, 4.0)
# plt.ylim(-0.25, 5.0)

# plt.xlabel("Energies (eV)")
# plt.ylabel("Density of states")

# plt.axhline(y=0, color="k", linestyle="--", linewidth=2)
# plt.legend()
# leg = plt.gca().get_legend()
# ltext = leg.get_texts()  # all the text.Text instance in the legend
# plt.setp(ltext, fontsize=30)
# plt.tight_layout()

# plt.legend()
# plt.xlabel("Density of States")
# plt.xlabel("Energies (eV)")





# Load CHGCAR (valence e- only) and add "empty" atom (I use Hydrogen)
# from pymatgen.io.vasp.outputs import Chgcar
# chgcar = Chgcar.from_file('CHGCAR')
# structure = chgcar.structure
# structure.append('H', [0.5,0.5,0.5])
# chgcar.write_file('CHGCAR_empty')


import os
from pymatgen.io.vasp.outputs import Chgcar

all_parchgs = [filename for filename in os.listdir() if "CHG" in filename]

for parchg in all_parchgs:
    try:
        chgcar = Chgcar.from_file(parchg)
        structure = chgcar.structure
        structure.append('H', [0.5,0.5,0.5]) # structure.append('H', [0.55555, 0.77778, 0.53770])
        chgcar.write_file(parchg + '_empty')
    except:
        pass


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


nelectron_data = get_nelectron_counts()
nelectron_data.update({'H': 0}) # I need to add this for the empty atoms


def run_and_workup_bader(file, ref, savefile, nelectron_data=nelectron_data):
    
    # delete the previous ACF.dat just in case
    subprocess.run(f'rm ACF.dat; ./bader {file} -ref {ref} > bader.out', shell=True)

    # After bader is ran, we want to look at the data
    dataframe, extra_data = parse_ACF(filename = "ACF.dat")

    # reload the structure used if I don't have it already
    structure = Chgcar.from_file(file).structure

    # Calculate the oxidation state of each site where it is simply the change in number of
    # electrons associated with it (from vasp potcar vs the bader charge)
    # I also add the element strings for filtering functionality
    elements = []
    oxi_state_data = []
    for site, site_charge in zip(structure, dataframe.charge.values):
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
    
    dataframe.to_csv(savefile)
    
    return dataframe, extra_data


normal = run_and_workup_bader("CHG_step1_empty", "CHGCAR_sum_empty", "normal.csv")


all_parchgs = [
    filename
    for filename in os.listdir()
    if "PARCHG" in filename and "_empty" in filename
]

import numpy
test = numpy.array([0]*4) #!!!!!!!!!!!!!!!!!! 135
for parchg in all_parchgs:
    dataframe, extra_data = run_and_workup_bader(parchg,parchg,parchg+"_result.csv")
    test = test + dataframe.charge.values

print("RESULT:", test)






dataframe = dataframe.assign(charge = test)
structure = Chgcar.from_file("CHG_empty").structure
# Calculate the oxidation state of each site where it is simply the change in number of
# electrons associated with it (from vasp potcar vs the bader charge)
# I also add the element strings for filtering functionality
elements = []
oxi_state_data = []
for site, site_charge in zip(structure, dataframe.charge.values):
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
dataframe.to_csv("decomposed_sums.csv")


# # Y2CF2
# bulk_ref = {
#     "Y": 2.386,
#     "C": -3.035,
#     "F": -0.868,
#     "H": 0,
#     }

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

raise MemoryError
