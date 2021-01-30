# -*- coding: utf-8 -*-

#-----------------------------------------------------------------------------

import copy

import numpy

from pymatgen.analysis.dimensionality import get_dimensionality_larsen
from pymatgen.analysis.local_env import ValenceIonicRadiusEvaluator

from pymatgen_diffusion.neb.full_path_mapper import FullPathMapper
from pymatgen_diffusion.neb.pathfinder import DistinctPathFinder

#-----------------------------------------------------------------------------

class DiffusionAnalysis:
    
    def __init__(
            
            self, 
            structure, # unitcell structure to analyze (must be pymatgen structure object)
            element_tested, # element whose mobility should be analyzed (e.g. 'F' or 'Li')
            oxidation_state, # desired oxidation state (e.g. '1-' or '1+')
            
            # general settings for symmetry, supercell, and pathway methods
            symprec=0.01, # symmetry precision cutoff
            min_sl_vector = 10, # target size of the supercell
            nimages = 6, # number of pathway images
            
            # cutoff settings for the pathway length 
            path_len_cutoff=5.0, # maximum length for a diffusion pathway
            path_len_cutoff_vsDmin=0.2, # maximum length of pathways relative to shortest possible path. For example, 0.2 includes paths up 20% longer than the min for the structure.
            
            # cutoff settings for the ionic radii overlap
            path_overlap_cutoff=1, # maximum change in ionic radii overlap along pathway
                        
            ):
        
        # Save the input settings for reference
        self.structure = structure
        self.element_tested = element_tested
        self.oxidation_state = oxidation_state
        self.ion_tested = element_tested + oxidation_state # ex: 'Li'+'1+' = 'Li1+'

        self.symprec = symprec
        self.min_sl_vector = min_sl_vector
        self.nimages = nimages

        self.path_len_cutoff = path_len_cutoff
        self.path_len_cutoff_vsDmin = path_len_cutoff_vsDmin
        
        self.path_overlap_cutoff = path_overlap_cutoff
        
        
    # PRECHECKS - Atomic Frac, Oxidation State, Etc. ----------------------------------
    def _prechecks(self):
        # check that structure has halide in <0.5 atomic fraction
        atm_frac = self.structure.composition.get_atomic_fraction(self.ion_tested)
        if atm_frac >= 0.5:
            print('Atomic fraction of the diffusing ion must be below 0.5')

        # Add oxidation state guess. There are multiple ways to do this:
        # structure.add_oxidation_state_by_guess()
        # OR
        # note that this class runs on top of BVanalyzer
        self.oxidation_check = ValenceIonicRadiusEvaluator(structure) # save this becuause the radii is used later
        self.structure = self.oxidation_check.structure
        
        # check that structure has ion in the proper oxidation state
        if self.ion_tested not in structure.composition:
            print('Target element is not in the desired oxidation state.')
        
        
    # STAGE 1  - Path distance --------------------------------------------------------
    def _stage1(self):
        
        # make approximately cubic LLL supercell, where each vector is at least min_sl_vector Angstroms
        self.structure_lll_supercell = structure.copy(sanitize=True) # Performs LLL-reduction
        supercell_size = [(min_sl_vector//length)+1 for length in self.structure_lll_supercell.lattice.lengths]
        self.structure_lll_supercell.make_supercell(supercell_size)
        
        # use pymatgen-diffusion to find all pathways less than path_len_cutoff
        dpf = DistinctPathFinder(
            structure = self.structure_lll_supercell,
            migrating_specie = self.ion_tested,
            max_path_length = self.path_len_cutoff, # in Angstroms 
            symprec = self.symprec, # Default is 0.1 which is very coarse
            perc_mode = None # Turns off ">1d" setting
            )
        
        # grab all pathway objects
        paths = dpf.get_paths()
        
        # if there are no output paths, errors will be thrown below so we check here
        if not paths:
            print('No pathways exist for the given ion, structure, symprec, and max_path_length.')
            
        # iterate through each and find the length of the shortest pathway 
        #!!! Are these ordered by length to begin with? That would save some time
        length_min = min([path.length for path in paths])
        
        # deletes paths that are X% (X = path_len_cutoff_vsDmin) longer than length_min
        max_length_allowed = length_min * self.path_len_cutoff_vsDmin
        self.paths = [path for path in paths if path.length <= max_length_allowed]
        
        
    # STAGE 2 - Diffusing ion's enviornment -------------------------------------------
    def _stage2(self):
        
        #!!! This function should be moved elsewhere and further developed in the future
        def get_ionic_radii_overlap(
                image_struct, 
                ion_index,
                oxidation_check=self.oxidation_check, #!!! is this line needed?
                ion_tested=self.ion_tested, #!!! is this line needed?
                ):
            
            moving_site = image_struct[path.iindex]
            moving_site_radius = self.oxidation_check.radii[self.ion_tested]
            moving_site_neighbors = image_struct.get_neighbors(moving_site, r=8.0, include_image=True) #!!! Hard-coding issue for cutoff radius?
            
            max_overlap_cation, max_overlap_anion, max_overlap_nuetral = [-999] * 3 # start as -999 to ensure its reset
            for neighbor_info in moving_site_neighbors:
                neighbor, distance, trash, trash = neighbor_info
                neighbor_radius = self.oxidation_check.radii[neighbor.species_string]
                overlap = moving_site_radius + neighbor_radius - distance
                # separate overlap analysis to oxidation types (+, -, or nuetral)
                if ('+' in neighbor.species_string) and (overlap > max_overlap_cation):
                    max_overlap_cation = overlap
                elif ('-' in neighbor.species_string) and (overlap > max_overlap_anion):
                    max_overlap_anion = overlap
                elif ('-' not in neighbor.species_string) and ('+' not in neighbor.species_string) and (overlap > max_overlap_nuetral):
                    max_overlap_nuetral = overlap
            
            # I convert to numpy here so I can quickly subtract arrays below
            return numpy.array(max_overlap_cation, max_overlap_anion, max_overlap_nuetral)
        
        valid_paths = []
        for path in self.paths:
            
            # we now run the idpp analysis on each pathway
            # The idpp relaxation is computationally expensive, so I only look at the 
            # start and midpoint images here.
            path_structures = path.get_structures(
                nimages=1, # for speed, I only do one image here
                vac_mode=True, # vacancy-based diffusion
                idpp=True, # IDPP relaxation of the pathway
                # **idpp_kwargs,#species = 'Li', # Default is None. Set this if I only want the ion to move
                )
                        
            # only grab the first two images (start and midpoint images)
            start_data = get_ionic_radii_overlap(path_structures[0], path.iindex)
            midpoint_data = get_ionic_radii_overlap(path_structures[1], path.iindex)
            
            # Compute the change in overlap for [cation, anion, nuetral]
            delta_overlaps = midpoint_data - start_data
            
            # See if any ion type changes ionic radii overlap over the allowed threshold
            if max(delta_overlaps) > self.path_overlap_cutoff:
                print("Pathway removed based on change in the diffusing ion's ionic radii overlap")
                pass
            else:
                valid_paths.append(path)
        
        # now that we've identified the valid paths, update the class's paths variable
        self.paths = valid_paths
        
        
    # STAGE 3 - Dimensionality --------------------------------------------------------
    def _stage3(self):
        
        #!!! This code should be made into a GetPathDimension class. I should also 
        #!!! consider rewritting the FullPathMapper class.
        
        # This runs much faster if we run this on the unitcell structure. So we make the 
        # same paths in the unitcell and then match them to the paths we have.
        dpf = DistinctPathFinder(
            structure = self.structure,
            migrating_specie = self.ion_tested,
            max_path_length = self.path_len_cutoff, # in Angstroms 
            symprec = self.symprec, # Default is 0.1 which is very coarse
            perc_mode = None # Turns off ">1d" setting
            )
        # grab all pathway objects
        paths_unitcell = dpf.get_paths()

        # we also need the structure_graph for dimensional analysis        
        fpm = FullPathMapper(
            self.structure, # use the unitcell for speed improvement
            self.ion_tested, 
            max_path_length=self.path_len_cutoff,
            symprec = self.symprec,)
        # we have to do this ourselves (looks like FullPathMapper was written by a beginner)
        fpm.populate_edges_with_migration_paths()
        fpm.group_and_label_hops()
        fpm.get_unique_hops_dict()
        # grab data for all edges of the structure graph as we access it repeatedly below
        edges = fpm.s_graph.graph.edges(data=True)
        
        # take the pathways that remain and run dimensional analysis 
        valid_paths = []
        for path in self.paths:
            
            # see which path is equivalent to the unitcell paths. We also need it's index
            # because the path index is used as the 'hop_label' in FullPathMapper
            for path_index, path_unitcell in paths_unitcell:
                if path == path_unitcell:
                    break
            assert(path == path_unitcell) #!!! to make sure our loop above worked successfully
            
            # Deleting all but a specific MigrationPath 
            # our target hop label is the path_index
             
            
            # DIMENSIONALITY (INDEPENDENT PATH)
            # make a deepcopy of the structuregraph because we will be deleting edges
            s_graph_temp = copy.deepcopy(fpm.s_graph)
            # Delete all but exact matches for the MigrationPath (which has a unique 'hop-label')
            for edge in edges:
                hop_label = edge[2]['hop_label']
                if hop_label != target_hop_label:
                    s_graph_temp.break_edge(
                        from_index=edge[0],
                        to_index=edge[1],
                        to_jimage=edge[2]['to_jimage'],
                        allow_reverse=False)
            dimensionality_ind = get_dimensionality_larsen(s_graph_test)
            
            # DIMENSIONALITY (CUMULATIVE BY LENGTH)
            #!!! So includes all paths that are shorter and DOES NOT take ionic radii overlap into account!
            #!!! I should consider changing this in the future.
            # make a deepcopy of the structuregraph because we will be deleting edges
            s_graph_temp = copy.deepcopy(fpm.s_graph)
            # Delete all but exact matches for the MigrationPath (which has a unique 'hop-label')
            for edge in edges:
                hop_label = edge[2]['hop_label']
                if hop_label != target_hop_label:
                    s_graph_temp.break_edge(
                        from_index=edge[0],
                        to_index=edge[1],
                        to_jimage=edge[2]['to_jimage'],
                        allow_reverse=False)
            dimensionality_ind = get_dimensionality_larsen(s_graph_test)
            
            
            
            if dimensionality_ind == 0:
                print('Pathway removed for not being periodic (>0d) on its own.')
                pass
            else:
                valid_paths.append(path)
            
            # EXTRA CODE
            # This line may be helpful when debugging. Try comparing before/after graphs.
            # edge_labels = numpy.array([d['hop_label'] for u, v, d in fpm.s_graph.graph.edges(data=True)])
            # These are other methods of breaking graph edges that I ended up not using
            # fpm.s_graph.break_edge(from_index, to_index, to_jimage=None, allow_reverse=False)
            # fpm.s_graph.graph.remove_edge(0,0)
            
            
        
        # now that we've identified the valid paths, update the class's paths variable
        self.paths = valid_paths
        
        pass
    
        #### STAGE 4 - Rough Energy Calc (start vs. mid) ------------------------------
        
        #### STAGE 5 - Rough Energy Calc (end) ----------------------------------------
        
        #### STAGE 6 ------------------------------------------
    
    
    
    
    def __workup__(self, mp_id = None, full_calc = True):
        pass
    
    def precheck(self):
        pass
    
    def full_analysis(self):
        pass
    
    def pathFinder(self):
        pass
    
    def getUniquePaths(self, cutoff_prec = 0.001):
        pass
    
    def getUniquePathDimension(self, cutoff_prec = 0.001):
        pass
    
    def IDPP_calcs_makefiles(self, preview = False, tol=3, makeVASPfiles = False, overlapanalysis = True):
        pass
    
    def import_results(self, output_xml="vasprun.xml", error_file = 'error_summary.txt'):
        pass
    
    def organize_and_plot_results(self, full_calc = True, filename = 'plot.png'):
        pass

#-----------------------------------------------------------------------------

# Loading an example structure
from pymatgen import MPRester
mpr = MPRester("2Tg7uUvaTAPHJQXl")
structure = mpr.get_structure_by_material_id("mp-22526")
# Y2CI2  # 1206803
# Ca2NCl # 22936
# LiCoO2 # 22526

structure = structure.copy(sanitize=True)

#-----------------------------------------------------------------------------

# check that structure has halide in <0.5 atomic fraction
atm_frac = structure.composition.get_atomic_fraction('Li')
if atm_frac >= 0.5:
    print('FAILED CHECK')

# add oxidation state guess
# structure.add_oxidation_state_by_guess()
# OR
# note that this class runs on top of BVanalyzer
from pymatgen.analysis.local_env import ValenceIonicRadiusEvaluator
structure = ValenceIonicRadiusEvaluator(structure).structure

# check that structure has ion in the proper oxidation state
if 'Li1+' not in structure.composition:
    print('FAILED CHECK')

# make approximately cubic LLL supercell of at least 10x10x10 Angstroms
min_sl_vector = 5
structure_lll_supercell = structure.copy(sanitize=True) # Performs LLL-reduction
supercell_size = [(min_sl_vector//length)+1 for length in structure_lll_supercell.lattice.lengths]
structure_lll_supercell.make_supercell(supercell_size)

#-----------------------------------------------------------------------------

from pymatgen_diffusion.neb.pathfinder import DistinctPathFinder

dpf = DistinctPathFinder(
    structure = structure_lll_supercell, #!!! can I do prechecks without a supercell?
    migrating_specie = 'Li1+',
    max_path_length = 6, # in Angstroms 
    symprec = 0.1, # Default is 0.1 which is very coarse
    perc_mode = None # Turns off ">1d" setting
    )

paths = dpf.get_paths()

path = paths[15]
length = path.length
# path_structures = path.get_structures(
#     nimages=5, 
#     vac_mode=True,
#     idpp=True,
#     # **idpp_kwargs,
#     #species = 'Li', # Default is None. Set this if I only want one to move
#     )
path.write_path('test15.cif', nimages=10, idpp=False, species = None,)

# write to cif file to visualize
dpf.write_all_paths('test.cif', nimages=10, idpp=False) # for speed, species kwarg isnt accepted here

#-----------------------------------------------------------------------------

#!!! Limit paths to those 20% longer than the shortest

#!!! Remove paths based on Ionic Radii Overlap Change

#!!! Ewald Energy

#-----------------------------------------------------------------------------

from pymatgen_diffusion.neb.full_path_mapper import FullPathMapper

fpm = FullPathMapper(
    structure, #!!! can I do prechecks without a supercell?
    'I', 
    max_path_length=5)

# we have to do this ourselves (FullPathMapper was written by a beginner)
fpm.populate_edges_with_migration_paths()
fpm.group_and_label_hops()
fpm.get_unique_hops_dict()

#-----------------------------------------------------------------------------

import numpy as np
edge_labels = np.array([d['hop_label'] for u, v, d in fpm.s_graph.graph.edges(data=True)])

# Test out deleting all but a specific MigrationPath (which has a unique 'hop-label')
import copy
s_graph_test = copy.deepcopy(fpm.s_graph)
target_hop_label = 0 #!!! SET THIS
edges = fpm.s_graph.graph.edges(data=True) 
for edge in edges:
    hop_label = edge[2]['hop_label']
    if hop_label != target_hop_label:
        s_graph_test.break_edge(from_index=edge[0],
                               to_index=edge[1],
                               to_jimage=edge[2]['to_jimage'],
                               allow_reverse=False)
edge_labels_test = np.array([d['hop_label'] for u, v, d in s_graph_test.graph.edges(data=True)])

from pymatgen.analysis.dimensionality import get_dimensionality_larsen
dimensionality = get_dimensionality_larsen(s_graph_test)

# These are other methods of breaking graph edges that I ended up not using
# fpm.s_graph.break_edge(from_index, to_index, to_jimage=None, allow_reverse=False)
# fpm.s_graph.graph.remove_edge(0,0)

#-----------------------------------------------------------------------------

# make the VASP input files for a given path
from pymatgen.io.vasp.sets import MPStaticSet

filename_folder_edge = filename_folder + "/EdgeIndex_" + str(edge_index)
os.mkdir(filename_folder_edge) 
for struct_index in range(len(idpp_structs)):
    filename_folder_edge_image = filename_folder_edge + "/ImageIndex_" + str(struct_index)
    MPStaticSet(idpp_structs[struct_index], user_incar_settings={"ISYM":0}).write_input(filename_folder_edge_image) 

#-----------------------------------------------------------------------------

# run ionic radii overlap analysis

# METHOD 1
# Finding max change in anion and cation overlap
overlap_data_cations, overlap_data_anions, overlap_data_nuetral = [], [], []
for struct_index in range(len(idpp_structs)):
    image_struct = idpp_structs[struct_index]
    moving_site = image_struct[site1_shifted_index]
    moving_site_neighbors = idpp_structs[struct_index].get_neighbors(moving_site, r=8.0, include_image=True)
    moiving_site_radius = self.oxidation_check.radii[self.ion_tested]
    max_overlap_cation, max_overlap_anion, max_overlap_nuetral = -999, -999, -999 # reset value for each image
    for neighbor_info in moving_site_neighbors:
        neighbor, distance, trash, trash = neighbor_info
        neighbor_radius = self.oxidation_check.radii[neighbor.species_string]
        overlap = moiving_site_radius + neighbor_radius - distance
        # separate overlap analysis to oxidation types (+, -, or nuetral)
        if ('+' in neighbor.species_string) and (overlap > max_overlap_cation):
            max_overlap_cation = overlap
        elif ('-' in neighbor.species_string) and (overlap > max_overlap_anion):
            max_overlap_anion = overlap
        elif ('-' not in neighbor.species_string) and ('+' not in neighbor.species_string) and (overlap > max_overlap_nuetral):
            max_overlap_nuetral = overlap
    overlap_data_cations.append(max_overlap_cation)
    overlap_data_anions.append(max_overlap_anion)
    overlap_data_nuetral.append(max_overlap_nuetral) 
# make lists into relative values
overlap_data_cations_rel = [(image - overlap_data_cations[0]) for image in overlap_data_cations]
overlap_data_anions_rel = [(image - overlap_data_anions[0]) for image in overlap_data_anions]
overlap_data_nuetral_rel = [(image - overlap_data_nuetral[0]) for image in overlap_data_nuetral]
# append to self.unique_edges[edge]
edge.append([overlap_data_cations_rel,overlap_data_anions_rel, overlap_data_nuetral_rel])
#plotting
# pyplot.figure(figsize=(5,3), dpi=80)
# pyplot.plot(range(self.nimages+1),overlap_data_cations_rel, 'o-', label='Cation')
# pyplot.plot(range(self.nimages+1),overlap_data_anions_rel, 'o-', label='Anion')
# pyplot.plot(range(self.nimages+1),overlap_data_nuetral_rel, 'o-', label='Nuetral')
# pyplot.legend(loc='upper right',title='Neighbor Type', fontsize=8)    
# pyplot.xlabel('Diffusion Progress')
# pyplot.xticks([0, self.nimages + 1], [r'$Start$', r'$End$'])
# pyplot.ylabel('Max Overlap (A)') 
# pyplot.tight_layout()
# pyplot.savefig(filename_folder + "edgeoverlap_" + str(edge_index))
# pyplot.show()
# pyplot.close()

# METHOD 2
from matminer.featurizers.site import EwaldSiteEnergy
sitefingerprint_method = EwaldSiteEnergy(accuracy=3) # 12 is default
# #!!! requires oxidation state decorated structure

images = path.get_structures(
    nimages=5, 
    vac_mode=True,
    idpp=True,
    # **idpp_kwargs,
    #species = 'Li', # Default is None. Set this if I only want one to move
    )

energy_ewald = []
for image in images:
    image_struct = idpp_structs[struct_index]
    # moving_site = image_struct[site1_shifted_index]
    image_fingerprint = numpy.array(sitefingerprint_method.featurize(image_struct, site1_shifted_index))
    image_fingerprint = image_fingerprint[1:] * (1/(numpy.array(range(len(image_fingerprint))))**2)[1:] #!!! RDF Scale down
    fingerprints.append(image_fingerprint)
# I don't want to save the full fingerprints, so I save the distances instead
# The distances are relative to the starting structure
energies_ewald = []
