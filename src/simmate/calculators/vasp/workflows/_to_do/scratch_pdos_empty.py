# -*- coding: utf-8 -*-

import subprocess
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
            "LCHARG": True,  # write CHGCAR
            "LAECHG": True,  # write AECCAR0, AECCAR1, and AECCAR2
            "LWAVE": True,  # write WAVECAR
            "NSW": 0,  # single energy calc
            "PREC": "Accurate",  # !!! USE Accurate WHEN NOT DOING BADELF
            "IVDW": 12,  # van der waals correction
            "ISMEAR": 0,  # Guassian smearing = 0 if system unknown!!!!!!!!!!!
            "SIGMA": 0.060,
            # 'NBANDS': 643, # Calculate more bands than normal (extra empty)
            "SYMPREC": 1e-8,  # !!! CUSTODIAN FIX - dont use unless needed
            # 'ISYM': 0,
            # 'NGX': 100,
            # 'NGY': 100,
            # 'NGZ': 100,
            "NGXF": 100,
            "NGYF": 100,
            "NGZF": 100,
            "NCORE": 8,
            #!!! TESTING
            # ELFCAR (optional)
            # 'LELF': True, # write ELFCAR
            # 'NPAR': 1, # Must be set if LELF is set to True
        },
        "KPOINTS": {"reciprocal_density": 100},
        "POTCAR_FUNCTIONAL": "PBE_54",
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
            "EDIFF": 1.0e-07,
            "EDIFFG": -1e-04,
            "ENCUT": 520,
            "ISIF": 3,  # !!! do I want this..?
            "ISMEAR": 0,  # Guassian smearing #!!! read docs!
            "LCHARG": True,  # write CHGCAR
            "LAECHG": True,  # write AECCAR0, AECCAR1, and AECCAR2
            # "LWAVE": True,
            "NSW": 0,  # single energy calc
            "PREC": "Accurate",  # !!! USE Accurate WHEN NOT DOING BADELF
            "IVDW": 12,  # van der waals correction
            "ISMEAR": -5,  # Guassian smearing ##### <<<<<<<<< Changed from the first calc
            # "SIGMA": 0.060, ##### <<<<<<<<< Changed from the first calc
            # 'NBANDS': 643, # Calculate more bands than normal (extra empty)
            "SYMPREC": 1e-8,  #!!! CUSTODIAN FIX - dont use unless needed
            "ISYM": 2,
            "NGXF": 100,
            "NGYF": 100,
            "NGZF": 100,
            "NCORE": 8,
            #!!! TESTING
            # ELFCAR (optional)
            # 'LELF': True, # write ELFCAR
            # 'NPAR': 1, # Must be set if LELF is set to True
            # PDOS
            "ISTART": 1,  # continuation file -- read the WAVECAR
            "ICHARG": 11,
            "LORBIT": 1,  #!!! use 11 if you don't want to set radii and 1 if you do
            # 'RWIGS': '', #!!! SET BELOW AND SET RADII IN SAME ORDER AS POSCAR
            "NEDOS": 2001,  # number of grid states for evaluating DOS
            # NBANDS, EMIN/EMAX are some others parameters that I can consider
        },
        "KPOINTS": {
            "reciprocal_density": 300
        },  ##### <<<<<<<<< Changed from the first calc
        "POTCAR_FUNCTIONAL": "PBE_54",
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


import pandas


def parse_ACF(filename="ACF.dat"):

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
        data=bader_data,
        columns=headers,
    )

    # Extra data is included in the footer that we can grab too. For each line, the data
    # is a float that is at the end of the line, hence the split()[-1].
    extra_data = {
        "vacuum_charge": float(lines[-3].split()[-1]),
        "vacuum_volume": float(lines[-2].split()[-1]),
        "nelectrons": float(lines[-1].split()[-1]),
    }

    return dataframe, extra_data


# -----------------------------------------------------------------------------

# if this is the starting point...
from pymatgen.core.structure import Structure

structure = Structure.from_file("Y2C.cif")
structure = structure.get_primitive_structure()
structure = structure.copy(sanitize=True)
calc = StaticEnergyCalc(structure)
# save the calc files
calc.write_input(".")

# -----------------------------------------------------------------------------

# RUN STATIC ENERGY CALC

print("Running vasp...")

# run vasp
subprocess.run(
    "module load vasp; mpirun -np 144 vasp_std > vasp.out",
    shell=True,
)

# -----------------------------------------------------------------------------

# RUN BADER ANALYSIS

subprocess.run("cp CHG CHG_step1", shell=True)
subprocess.run("./chgsum.pl AECCAR0 AECCAR2 > addingcharges.out", shell=True)
subprocess.run("./bader CHG -ref CHGCAR_sum > bader.out", shell=True)
# subprocess.run('./bader CHG -ref ELFCAR > bader.out', shell=True)

# After bader is ran, we want to look at the data
dataframe, extra_data = parse_ACF(filename="ACF.dat")

# Update the NonSCFCalc settings with RWIGS
# ...based off min-dist
# NonSCFCalc.CONFIG["INCAR"].update({"RWIGS": str(dataframe.min_dist.values)[1:-1]})
# ...based off total volume
# import math
# import numpy
# radii_from_vol = numpy.array([((3*volume)/(4*math.pi))**(1/3) for volume in dataframe.atomic_vol.values])
# NonSCFCalc.CONFIG["INCAR"].update({"RWIGS": str(radii_from_vol)[1:-1]})

NonSCFCalc.CONFIG["INCAR"].update({"RWIGS": "1.584 1.699 1.552"})

# -----------------------------------------------------------------------------

structure = Structure.from_file("CONTCAR")
calc = NonSCFCalc(structure)

# save the calc files
calc.write_input(".")

# -----------------------------------------------------------------------------

#######
# Now run this calculation
# And then move the results back to the same directory
#!!! If you want an empty atom, you must manually add this text at the bottom of the POSCAR
# Empty (spheres)
# 1
# 0.000000 0.000000 0.000000
#!!! I also need to set LORBIT to 1 instead of 11
#!!! I need to set the RWIGS tag too so that it knows what radius the sphere has
#######


# Now run this calculation

print("Running vasp...")

subprocess.run(
    "module load vasp; mpirun -np 144 vasp_std > vasp.out",
    shell=True,
)
# /nas/longleaf/apps-dogwood/vasp/5.4.4/bin/vasp_std

# -----------------------------------------------------------------------------

# from pymatgen.io.vasp.outputs import Vasprun

# xmlReader = Vasprun(filename= "vasprun.xml",
#                     parse_dos = True,
#                     parse_eigen = True,
#                     parse_projected_eigen = True, #!!! **Note that this can take an extreme amount of time and memory.** So use this wisely.
#                     parse_potcar_file = True,
#                     exception_on_bad_xml = True)

# # update the structure (really this should be the same)
# structure = xmlReader.structures[0]

# If you added an ampty sphere, we need to take that into accound here!
# pymatgen doesn't add the empty atom so we must do that ourselves
#!!! I added custom code to pymatgen.io.vasp.outputs.Vasprun.compelete_dos
# from pymatgen.core.periodic_table import DummySpecie
# dummy_element = DummySpecie()
# structure.append(dummy_element, [0.5,0.5,0.5])

# # grab both the total density of states and all the partial densitry of states
# complete_dos = xmlReader.complete_dos

# # now we want to plot the DOS
# from pymatgen.electronic_structure.plotter import DosPlotter

# ########## PLOT 1

# plotter = DosPlotter(zero_at_efermi = True,
#                       stack = False,
#                       sigma=0.05) #!!! set to None if you dont want smoothing

# # plot the total DOS first
# plotter.add_dos("Total DOS", complete_dos)


# # now lets get the pDOS
# pdos = complete_dos.get_element_dos()
# for element in structure.composition:
#     # grab the single element pdos
#     element_pdos = pdos[element]
#     # add it to the plot
#     plotter.add_dos(element.symbol, element_pdos)

# # plotter.get_plot()
# plotter.get_plot(xlim=[-4.5,4.5], ylim=[-0.25,8])

# ########## PLOT 2

# alternatively I can plot by site
# I start by resetting the plot

# from scipy.integrate import trapz

# plotter = DosPlotter(zero_at_efermi = True,
#                       stack = False,
#                       sigma=None) #!!! 0.05set to None if you dont want smoothing

# # plot the total DOS first
# plotter.add_dos("Total DOS", complete_dos)

# for i, site in enumerate(structure):
#     # grab the single element pdos
#     site_pdos = complete_dos.get_site_dos(site)
#     # add it to the plot
#     plotter.add_dos(i, site_pdos)

#     # INTEGRATE
#     den = site_pdos.densities # .get_smeared_densities(0.05)
#     den = [den[key] for key in den.keys()]
#     den = den[0] # + den[1] if spin polarized
#     eng = site_pdos.energies - site_pdos.efermi
#     eng = [value for value in eng if value < 0]
#     den = den[:len(eng)]


#     # INTEGRATE
#     area = trapz(y=den, x=eng)

#     symbol = site.specie.symbol
#     if symbol == 'F' or symbol == 'Cl' or symbol == 'Na':
#         print(site.specie.symbol  + ': ' + str(7 - area))
#     elif symbol == 'C':
#         print(site.specie.symbol  + ': ' + str(4 - area))
#     elif symbol == 'Y':
#         print(site.specie.symbol  + ': ' + str(11 - area))
#         # print(site.frac_coords)

# plot = plotter.get_plot()
# plot.savefig("pdos.png")

# plot = plotter.get_plot(xlim=[-5,5], ylim=[-0.25,5])
# plot.savefig("pdos_zoom.png")

# ########## PLOT 3

# # alternatively I can plot the sum of spins up/down

# # for this, I can't use the pymatgen plotter function

# import matplotlib.pyplot as plt
# from scipy.integrate import trapz #!!! this isn't giving me accurate integrations
# # from numpy import trapz

# # Create a new figure of size 8x6 points, using 100 dots per inch
# plt.figure(figsize=(10,6), dpi=80)

# # Create a new subplot from a grid of 1x1
# plt.subplot(111)

# pdos = complete_dos.get_element_dos()
# for element in structure.composition:
#     # grab the single element pdos
#     element_pdos = pdos[element]
#     # add it to the plot
#     den = element_pdos.densities # .get_smeared_densities(0.05)
#     den = [den[key] for key in den.keys()]
#     den = den[0] # + den[1] #!!! with y2c only
#     eng = element_pdos.energies - element_pdos.efermi

#     # INTEGRATE
#     area = trapz(y=den[:1677], x=eng[:1677]) #1263
#     print(element.symbol  + ': ' + str(area))

#     plt.plot(eng, den, label=element.symbol, linewidth=2.5, linestyle="-")

# plt.xlim(-4.0,4.0)
# plt.ylim(-0.25,5.0)

# plt.xlabel('Energies (eV)')
# plt.ylabel('Density of states')

# plt.axhline(y=0, color='k', linestyle='--', linewidth=2)
# plt.legend()
# leg = plt.gca().get_legend()
# ltext = leg.get_texts()  # all the text.Text instance in the legend
# plt.setp(ltext, fontsize=30)
# plt.tight_layout()

# plt.legend()
# plt.xlabel('Density of States')
# plt.xlabel('Energies (eV)')
