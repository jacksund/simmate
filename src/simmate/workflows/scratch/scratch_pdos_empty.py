# -*- coding: utf-8 -*-

from pymatgen.core.structure import Structure
from pymatgen.io.vasp.sets import MPRelaxSet

# load the structure's cif
structure = Structure.from_file('Y2CF2.cif')

# setup the energy calc with default settings
calc = MPRelaxSet(structure)

# save the calc files
calc.write_input('Y2CF2_geomopt_input')

#######
# Now run this calculation 
# And then move the results back to the same directory
#######

from pymatgen.io.vasp.sets import MPStaticSet

# setup the energy calc with default settings
# calc = MPStaticSet.from_prev_calc('Y2CF2_geomopt_output')

# if this is the starting point...
from pymatgen.core.structure import Structure
structure = Structure.from_file('Y2C_TS.cif')
settings={'ISMEAR': 0, # tetrahedral method
          'ENCUT': 800, 
          'EDIFF': 1e-8,
          'EDIFFG': -1e-4,
          'IVDW': 12,
          'SIGMA': 0.06,
          'LAECHG': False,
          'LVHAR': True,
          'ISPIN': 1,
          'LREAL': False,
          'MAGMOM': None,
          }
calc = MPStaticSet(structure,
                   user_incar_settings=settings,
                   user_kpoints_settings={'reciprocal_density': 500})

# save the calc files
calc.write_input('Y2CF2_TS_energy_input')

#!!! currently I get a warning in the VASP output to set LREAL=.FALSE. (I currently have it set to AUTO)

#######
# Now run this calculation 
# And then move the results back to the same directory
#######

from pymatgen.io.vasp.sets import MPNonSCFSet
settings={
          'ISYM': 0,
          
          #!!! If using custom radii...
          # 'LORBIT': 1,
          # 'RWIGS': '1.553 1.632 1.515', # Y, C, F radii
          
          }
calc = MPNonSCFSet.from_prev_calc('Y2CF2_TS_energy_output', 
                                  mode='uniform', 
                                  reciprocal_density=1000, 
                                  optics=False,
                                  user_incar_settings=settings)

calc.write_input('Y2CF2_TS_pdos_input')

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

# move into the correct folder first!
# import os
# os.chdir('Y2C_pdos_output')

from pymatgen.io.vasp.outputs import Vasprun

xmlReader = Vasprun(filename= "vasprun.xml",
                    parse_dos = True,
                    parse_eigen = True,
                    parse_projected_eigen = True, #!!! **Note that this can take an extreme amount of time and memory.** So use this wisely.
                    parse_potcar_file = True,
                    exception_on_bad_xml = True)

# update the structure (really this should be the same)
structure = xmlReader.structures[0]

# If you added an ampty sphere, we need to take that into accound here!
# pymatgen doesn't add the empty atom so we must do that ourselves
#!!! I added custom code to pymatgen.io.vasp.outputs.Vasprun.compelete_dos
# from pymatgen.core.periodic_table import DummySpecie
# dummy_element = DummySpecie()
# structure.append(dummy_element, [0.5,0.5,0.5])

# grab both the total density of states and all the partial densitry of states
complete_dos = xmlReader.complete_dos

# now we want to plot the DOS
from pymatgen.electronic_structure.plotter import DosPlotter

########## PLOT 1

plotter = DosPlotter(zero_at_efermi = True,
                     stack = False,
                     sigma=0.05) #!!! set to None if you dont want smoothing

# plot the total DOS first
plotter.add_dos("Total DOS", complete_dos)


# now lets get the pDOS
pdos = complete_dos.get_element_dos()
for element in structure.composition:
    # grab the single element pdos
    element_pdos = pdos[element]
    # add it to the plot
    plotter.add_dos(element.symbol, element_pdos)

plotter.get_plot()
# plotter.get_plot(xlim=[-4.5,4.5], ylim=[-0.25,100])

########## PLOT 2

# alternatively I can plot by site
# I start by resetting the plot

from scipy.integrate import trapz

plotter = DosPlotter(zero_at_efermi = True,
                      stack = False,
                      sigma=0.05) #!!! set to None if you dont want smoothing

# plot the total DOS first
plotter.add_dos("Total DOS", complete_dos)

for i, site in enumerate(structure):
    # grab the single element pdos
    site_pdos = complete_dos.get_site_dos(site)
    # add it to the plot
    plotter.add_dos(i, site_pdos)
    
    # INTEGRATE
    den = site_pdos.densities # .get_smeared_densities(0.05)
    den = [den[key] for key in den.keys()]
    den = den[0] # + den[1] #!!! with y2c only
    eng = site_pdos.energies - site_pdos.efermi
    
    # INTEGRATE
    area = trapz(y=den[:1677], x=eng[:1677]) 
    
    symbol = site.specie.symbol
    if symbol == 'F':
        print(site.specie.symbol  + ': ' + str(7 - area))
    elif symbol == 'C':
        print(site.specie.symbol  + ': ' + str(4 - area))
    if symbol == 'Y':
        print(site.specie.symbol  + ': ' + str(11 - area))
        # print(site.frac_coords)
    
plotter.get_plot(xlim=[-5,5], ylim=[-0.25,5])

########## PLOT 3

# alternatively I can plot the sum of spins up/down

# for this, I can't use the pymatgen plotter function

import matplotlib.pyplot as plt
from scipy.integrate import trapz #!!! this isn't giving me accurate integrations
# from numpy import trapz

# Create a new figure of size 8x6 points, using 100 dots per inch
plt.figure(figsize=(10,6), dpi=80)

# Create a new subplot from a grid of 1x1
plt.subplot(111)

pdos = complete_dos.get_element_dos()
for element in structure.composition:
    # grab the single element pdos
    element_pdos = pdos[element]
    # add it to the plot
    den = element_pdos.densities # .get_smeared_densities(0.05)
    den = [den[key] for key in den.keys()]
    den = den[0] # + den[1] #!!! with y2c only
    eng = element_pdos.energies - element_pdos.efermi
    
    # INTEGRATE
    area = trapz(y=den[:1677], x=eng[:1677]) #1263
    print(element.symbol  + ': ' + str(area))
    
    plt.plot(eng, den, label=element.symbol, linewidth=2.5, linestyle="-")

plt.xlim(-4.0,4.0)
plt.ylim(-0.25,5.0)

plt.xlabel('Energies (eV)')
plt.ylabel('Density of states')

plt.axhline(y=0, color='k', linestyle='--', linewidth=2)
plt.legend()
leg = plt.gca().get_legend()
ltext = leg.get_texts()  # all the text.Text instance in the legend
plt.setp(ltext, fontsize=30)
plt.tight_layout()

plt.legend()
plt.xlabel('Density of States')
plt.xlabel('Energies (eV)')

