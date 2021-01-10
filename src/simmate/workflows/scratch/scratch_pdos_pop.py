# -*- coding: utf-8 -*-

from pymatgen.io.vasp.sets import DictSet

#!!! The warning that is raised here is because there is no YAML! It can be ignored
class MyCustomSet(DictSet):

    CONFIG = {'INCAR': {'EDIFF': 1.0e-07,
                        'EDIFFG': -1e-04, 
                        'ENCUT': 500,
                        'IBRION': -1,
                        'ISIF': 3,
                        'ISMEAR': 0, # Guassian smearing
                        'SIGMA': 0.060,
                        'ISTART': 1, # read wavecar
                        
                        'LCHARG': True, # write CHGCAR
                        'LWAVE': True,
                        'NSW': 0, # single energy calc
                        'PREC': 'Accurate',
                        'NELM': 100,
                        'IVDW': 12,
                        #'NPAR': 1, #!!! VASP says this is slower...
                        
                        #'ICHARG': 11, # find
                        
                        #!!! CHANGE THESE OPTIONS BASED OFF OF YOUR SYSTEM
                        #'NBANDS': 100,
                        'LORBIT': 2, #!!! use 11 if you don't want to set radii and 2 if you do
                        'RWIGS': '1.747 1.721 1.809', #!!! SET RADII IN SAME ORDER AS POSCAR
                        'NEDOS': 1000, # number of grid states for evaluating DOS
                        },
              'KPOINTS': {'reciprocal_density': 50},
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
structure = Structure.from_file('Sr2NF.cif') #!!! NAME YOUR INPUT STRUCTURE FILE HERE
structure = structure.get_primitive_structure()

# write the vasp input files
MyCustomSet(structure).write_input(".")

#-----------------------------------------------------------------------------

print('Running vasp...')

# run vasp
import subprocess
subprocess.run('module load vasp; mpirun -np 12 vasp > vasp.out', shell=True)

#-----------------------------------------------------------------------------

print('Working up...')
# import the VASP results
from pymatgen.io.vasp.outputs import Vasprun
xmlReader = Vasprun(filename= "vasprun.xml",
                    parse_dos = True,
                    parse_eigen = True,
                    parse_projected_eigen = True, #!!! **Note that this can take an extreme amount of time and memory.** So use this wisely.
                    parse_potcar_file = True,
                    exception_on_bad_xml = True)


# grab the info we want
final_structure = xmlReader.structures[-1] # or Structure.from_file('CONTCAR')
final_energy = xmlReader.final_energy / final_structure.num_sites #!!! convert this to per_atom!
converged = xmlReader.converged

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
for element in final_structure.composition:
    # grab the single element pdos
    element_pdos = pdos[element]
    # add it to the plot
    plotter.add_dos(element.symbol, element_pdos)


# plotter.get_plot()
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

for i, site in enumerate(final_structure):
    # grab the single element pdos
    site_pdos = complete_dos.get_site_dos(site)
    # add it to the plot
    plotter.add_dos(i, site_pdos)
    
    # INTEGRATE
    den = site_pdos.densities # .get_smeared_densities(0.05)
    den = [den[key] for key in den.keys()]
    
    if len(den) == 1: # there is only + spin
        den = den[0]
    elif len(den) == 2: # there is +/- spins
        den = den[0] + den[1]
    
    # scale energy
    eng = site_pdos.energies - site_pdos.efermi
    
    # find index of fermi energy
    fermi_i = len([x for x in eng if x < 0])-1
    
    # INTEGRATE
    area = trapz(y=den[:fermi_i], x=eng[:fermi_i]) 
    
    
    
    symbol = site.specie.symbol
    if symbol in ['Ca','Sr']:
        print(site.specie.symbol  + ': ' + str(10 - area))
    elif symbol in ['N']:
        print(site.specie.symbol  + ': ' + str(5 - area))
    elif symbol in ['Y']:
        print(site.specie.symbol  + ': ' + str(11 - area))
    elif symbol in ['C']:
        print(site.specie.symbol  + ': ' + str(4 - area))
    elif symbol in ['Cl', 'F']:
        print(site.specie.symbol  + ': ' + str(7 - area))
    
    print("coords: " + str(site.frac_coords) + '\n')
    
# plotter.get_plot(xlim=[-5,5], ylim=[-0.25,5])

print('Done!')

#-----------------------------------------------------------------------------


