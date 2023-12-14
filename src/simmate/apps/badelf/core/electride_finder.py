# -*- coding: utf-8 -*-

from simmate.apps.badelf.core import Grid, PartitioningToolkit, VoxelAssignmentToolkit
from scipy.ndimage import label, find_objects, maximum_filter
from scipy.interpolate import RegularGridInterpolator
from scipy.optimize import curve_fit, fmin
import numpy as np
import math
from pymatgen.analysis.local_env import CrystalNN

class ElectrideFinder:
    """
    A class for finding electride sites from an ELFCAR.
    
    Args:
        grid : Grid
            A BadELF app Grid instance made from an ELFCAR.
    """
    
    def __init__(
            self,
            grid: Grid,
            ):
        self.grid = grid.copy()
    

    def gaussian_fit(coordinates, amplitude, x0, y0, z0, sigma_x, sigma_y, sigma_z):
        x, y, z = coordinates
        return amplitude * np.exp(
            -((x - x0)**2 / (2 * sigma_x**2)) - ((y - y0)**2 / (2 * sigma_y**2)) - ((z - z0)**2 / (2 * sigma_z**2))
        )
        
    def find_local_maxima(
            self,
            neighborhood_size=1, 
            threshold=None):
        """
        Find local maxima in a 3D numpy array.
        
        Args:
        - neighborhood_size: Size of the neighborhood for finding local maxima
        - threshold: Threshold for considering a point as a local maximum
        
        Returns:
        - List of tuples containing the coordinates of local maxima
        """
        elf_data = self.grid.total
        # Get padded data so that we can look at voxels at the edges
        padded_elf_data = np.pad(elf_data, neighborhood_size, mode="wrap")
        local_maxima = []
        maxima_values = []
        
        # Look across each voxel in the structure.
        for z in range(neighborhood_size, padded_elf_data.shape[0] - neighborhood_size):
            for y in range(neighborhood_size, padded_elf_data.shape[1] - neighborhood_size):
                for x in range(neighborhood_size, padded_elf_data.shape[2] - neighborhood_size):
                    neighborhood = padded_elf_data[z - neighborhood_size:z + neighborhood_size + 1,
                                       y - neighborhood_size:y + neighborhood_size + 1,
                                       x - neighborhood_size:x + neighborhood_size + 1]
                    max_value = np.max(neighborhood)
                    z_orig = z - neighborhood_size
                    y_orig = y - neighborhood_size
                    x_orig = x - neighborhood_size
                    if elf_data[z_orig, y_orig, x_orig] == max_value and (threshold is None or max_value > threshold):
                        local_maxima.append((z_orig+1, y_orig+1, x_orig+1))
                        maxima_values.append(elf_data[z_orig, y_orig, x_orig])
        
        return local_maxima, maxima_values
    
    def get_refined_local_maxima(
            self, 
            neighborhood_size: int = 2,
            voxel_maxima: list = None,
            ):
        """
        Fit a 3D Gaussian function around each local maximum.
        
        Args:
            neighborhood_size (int): 
                Size of the neighborhood for finding local maxima
            
            voxel_maxima (list):
                A list of maxima in voxel coordinates. Will be found automatically
                if not given.
        
        Returns:
            - List of local maxima in the structure in cartesian coordinates
        """
        # Define a 3D gaussian function that will be used to fit the regions
        # around each local maximum
        # def gaussian_fit(coordinates, amplitude, x0, y0, z0, sigma_x, sigma_y, sigma_z):
        #     x, y, z = coordinates
        #     return amplitude * np.exp(
        #         -((x - x0)**2 / (2 * sigma_x**2)) - ((y - y0)**2 / (2 * sigma_y**2)) - ((z - z0)**2 / (2 * sigma_z**2))
        #     )
        
        # elf_data = self.grid.total
        if voxel_maxima is None:
            voxel_maxima, voxel_values = self.find_local_maxima()
        maxima_cart_coords = []
        # maxima_values = []
        for voxel_maximum in voxel_maxima:
            cart_maximum = self.grid.get_cart_coords_from_vox(voxel_maximum)
            maxima_cart_coords.append(cart_maximum)
        
        #!!! Just using the exact voxel locations seems to give better results
        # than fitting to a gaussian
        # # Create a padded grid so that values around local maxima at an edge
        # # can be obtained
        # padded_elf_data = np.pad(elf_data, neighborhood_size, mode="wrap")
        
        # # Create a new list of maxima voxels adjusted for the padding.
        # padded_voxel_maxima = []
        # for maximum in voxel_maxima:
        #     # add the padded number to the voxel. Also remove 1 because these
        #     # valuse come in in voxel coord format.
        #     adjusted_maximum = [i+neighborhood_size-1 for i in maximum]
        #     padded_voxel_maxima.append(adjusted_maximum)
        
        # for max_point in padded_voxel_maxima:
        #     x, y, z = max_point
        #     # Get a [3,3,3] array of values around the voxel found to be a local
        #     # maximum
        #     neighborhood = padded_elf_data[x - neighborhood_size:x + neighborhood_size + 1,
        #                   y - neighborhood_size:y + neighborhood_size + 1,
        #                   z - neighborhood_size:z + neighborhood_size + 1,]
            
        #     # We are going to flatten this array into 1D so we need a list of
        #     # indices that maps the 1D array to the original 3D
        #     indices = np.indices(neighborhood.shape)
        #     original_indices = np.column_stack((indices[0].flatten(), indices[1].flatten(), indices[2].flatten()))
        #     xs, ys, zs = original_indices[ :,0], original_indices[ :,1], original_indices[ :,2]
            
        #     # Our voxel maximum is located at [1,1,1] in our 3D array so we make the
        #     # guess for the amplitute the value there. The guesses for x0,y0,z0
        #     # should also be 1,1,1 because we are likely to find the maximum
        #     # around there.
        #     initial_guess = (np.max(neighborhood), neighborhood_size, neighborhood_size, neighborhood_size, 1, 1, 1)
        #     # fit the curve to our faussian function and get the parameters back
        #     popt, _ = curve_fit(gaussian_fit, (xs,ys,zs), neighborhood.flatten(), p0=initial_guess)
            
        #     # convert the coords back to the original voxel grids indices.
        #     # We need to add back the neighborhood size twice because we removed
        #     # it twice. We also need to add x back and 1 to get to the proper
        #     # voxel coordinates ([1,1,1] at bottom corner)
        #     max_coord = [popt[1]+x+1-(2*neighborhood_size), popt[2]+y+1-(2*neighborhood_size), popt[3]+z+1-(2*neighborhood_size)]
            
        #     # Get the fit max value from the gaussian fit
        #     # max_value = gaussian_fit([popt[1],popt[2],popt[3]], popt[0], popt[1], 
        #     #                          popt[2], popt[3],popt[4], popt[5], popt[6])
        #     # convert to cartesian coords and append to list
        #     maxima_cart_coords.append(self.grid.get_cart_coords_from_vox(max_coord))
            # maxima_values.append(max_value)
        
        return maxima_cart_coords, voxel_values
            

    def find_electrides(
            self,
            local_maxima_coords: list = None,
            local_maxima_values: list = None,
            remove_old_electrides: bool = True,
            distance_cutoff: float = 1.6,
            elf_cutoff: float = 0.5,
            min_electride_radius: float = 0.8 
            ):
        #!!! The distance cutoff and min_electride_radius are fairly arbitrary
        # How should I find them instead?
        """
        Finds the electrides in a structure using an ELF grid.

        Parameters
        ----------
        local_maxima_coords : list, optional
            The coordinates of all local maxima in the grid. This will be found
            automatically if not set.
        local_maxima_values : list, optional
            The values at the local maxima. This will be found automatically if
            not set.
        remove_old_electrides : bool, optional
            Whether or not to remove any other electrides already placed in
            the system. It is generally recommended that structures without
            electrides are provided.
        distance_cutoff : float, optional
            The minimum distance the local maxima must be from an atom to be
            considered as a possible electride. The default is 1.19.
        elf_cutoff : float, optional
            The minimum elf value at the site to be considered a possible
            electride. The default is 0.5.
        min_electride_radius : float, optional
            The minimum elf radius around the maximum for it to be considered
            an electride. The default is 1.19 which is the radius of fluoride 
            in a 6 coordination environment.

        Returns
        -------
        A structure object with the found electride sites labeled with "He"
        dummy atoms.
        """
        grid = self.grid.copy()
        grid.regrid(desired_resolution=1000)
        
        if local_maxima_coords is None:
            local_maxima_coords, local_maxima_values = ElectrideFinder(grid).get_refined_local_maxima()
        
        structure = grid.structure
        if "He" in structure.symbol_set and remove_old_electrides:
            old_electride_sites = structure.indices_from_symbol("He")
            structure.remove_sites(old_electride_sites)
        
        cnn = CrystalNN()
        electride_coords = []
        for i, maximum_coords in enumerate(local_maxima_coords):
            # Check if the elf value is below the cutoff
            if local_maxima_values[i] < elf_cutoff:
                continue
            
            electride_structure = structure.copy()
            electride_structure.append("He", maximum_coords, coords_are_cartesian=True)
            _,_,electride_neighbors = cnn.get_nn_data(electride_structure, n=-1)

            most_neighbors = max(electride_neighbors)
            electride_neighbors = electride_neighbors[most_neighbors]
            # get distances to nearby atoms
            atom_distances = []
            for neighbor in electride_neighbors:
                if neighbor["site"].species_string != "He":
                    distance = math.dist(maximum_coords, neighbor["site"].coords)
                    atom_distances.append(distance)
            
            # check if minimum distance is too close to an atom:

            if min(atom_distances) < distance_cutoff:
                continue
            
            # get distances to min along lines to closest atoms
            electride_radius = PartitioningToolkit(grid).get_elf_ionic_radius(
                site=len(electride_structure)-1,
                structure=electride_structure,
                
                )
            # print(f"{maximum_coords} {min(atom_distances)} {electride_radius}")
            if electride_radius < min_electride_radius:
                continue
            
            # If the loop is still going, we consider this site an electride. We
            # add it to the list of electride sites.
            electride_coords.append(maximum_coords)
            # electride_coordinations.append(cnn.get_cn(electride_structure, n=-1))
            
        
        # Often the algorithm will find several electride sites right next to
        # eachother. This can be due to voxelation or because of oddly shaped
        # electrides. We want to combine these into one electride site.
        empty_structure = structure.copy()
        for coord in electride_coords:
            empty_structure.append("He", coord, coords_are_cartesian=True)
        
        # We are going to start a loop where we continuosly combine potential
        # electride sites until they are all combined. We start with an 
        # indicator for a while loop to check against
        all_combined = False
        # Now we loop over the electride sites
        while not all_combined:
            electride_indices = empty_structure.indices_from_symbol("He")
            # Assume that everything is combined.
            all_combined = True
            for electride_index in electride_indices:
                # Get any neighbors within 0.5 Angstrom of our electride. Because
                # one of our cutoffs earlier was that atoms had to be more than
                # 1.6 A away, we shouldn't find anything but other electride
                # sites in this range.
                site = empty_structure[electride_index]
                neighbors = empty_structure.get_neighbors(site, 0.5)
                if len(neighbors) > 0:
                    # Indicate that we still have things to combine
                    all_combined = False
                    # Add all neighboring electride indices to a list. Do the
                    # same for their coords
                    nearby_electride_indices = [neigh.index for neigh in neighbors]
                    nearby_electride_indices.append(electride_index)
                    nearby_electride_coords = [neigh.coords for neigh in neighbors]
                    nearby_electride_coords.append(site.coords)
                    
                    # Calculate the position of the new electride coord.
                    new_electride_coord = sum(nearby_electride_coords)/len(nearby_electride_coords)
                    
                    # remove the old sites from the structure
                    empty_structure.remove_sites(nearby_electride_indices)
                    # Add our new coord
                    empty_structure.append("He", new_electride_coord, coords_are_cartesian=True)
                    break
                    # We now go back to the beginning of the while loop. We get
                    # a new set of electride sites from our updated empty_structure
                    # and repeate everything
        
        electride_coordinations = []
        # The electride indices are the same as our last while loop
        for electride_index in electride_indices:
            electride_coord = empty_structure[electride_index].coords
            electride_structure = structure.copy()
            electride_structure.append("He", electride_coord, coords_are_cartesian=True)
            electride_coordinations.append(cnn.get_cn(electride_structure, -1))
        
        return empty_structure, electride_coordinations
                    
                
        
        # # We now need to look through and see if any found electride sites are
        # # very close. If they are we want to combine them. This can happen I
        # # believe due to voxelation
        # empty_structure = structure.copy()
        # # create structure with all electrides
        # for electride in electride_coords:
        #     empty_structure.append("He", electride, coords_are_cartesian=True)
        
        # # Create an indicator that all nearby electrides have been combined
        # all_combined = False
        # # Loop over the process for combining electrides until all nearby ones
        # # have been
        # while all_combined == False:
        #     # Get the indices of the electride sites
        #     electride_sites = empty_structure.indices_from_symbol("He")
        #     # Assume all electrides have been combined
        #     all_combined = True
        #     # Iterate over each electride
        #     for site_index in electride_sites:
        #         # Get the pymatgen Site class object for this site and its nearest
        #         # neighbor. Then get the distance. We want to check if they are
        #         # close (somewhat arbitrarily we set this to .3 Angstrom)
        #         site = empty_structure[site_index]
        #         neighbor = empty_structure.get_neighbors(site, 15)[0]
        #         if neighbor.species_string != "He":
        #             continue
        #         distance = math.dist(site.coords, neighbor.coords)
        #         if distance < 0.3:
        #             # These haven't been combined so we set all_combined to false.
        #             # We remove the two sites and add a new one at the midpoint
        #             # between them.
        #             all_combined = False
        #             empty_structure.remove_sites([site_index, neighbor.index])
        #             site_to_add = np.round(((empty_structure[site_index].coords + neighbor.coords)/2),2)
        #             empty_structure.append("He", site_to_add, coords_are_cartesian=True)
        #             break
        
        # Now we want to get the coordination environment of all of the electrides
        # for electride_index in electride_sites
                
        # return empty_structure
        
        # sites_to_remove = []
        # coords_to_append = []
        # # Get indices of the electrides
        # electride_sites = empty_structure.indices_from_symbol("He")
        # # Get the single closest atom to each atom in the system
        # closest_neighbors = PartitioningToolkit(grid).get_set_number_of_neighbors(1)
        # # Loop over the electride sites in the empty_structure
        # for site_index in electride_sites:
        #     # If the site is already in the sites to remove, skip it
        #     # if site_index in sites_to_remove:
        #     #     continue
            
        #     neighbor = closest_neighbors[site_index][0]
        #     # If the neighbor index is already in the sites to remove, skip it.
        #     # if neighbor.index in sites_to_remove:
        #     #     continue
        #     # Get the distance between the site and its neighbor. If it is less
        #     # than 0.3 A we want to remove both sites and get the point exactly
        #     # between them. We append this middle point to our list of coords to
        #     # add.
        #     distance = math.dist(empty_structure[site_index].coords, neighbor.coords)
        #     if distance < 0.3:
        #         sites_to_remove.extend([site_index, neighbor.index])
        #         site_to_add = np.round(((empty_structure[site_index].coords + neighbor.coords)/2),2)
        #         coords_to_append.append(site_to_add)
        
        # empty_structure.remove_sites(sites_to_remove)
        
        # for electride in coords_to_append:
        #     empty_structure.append("He", electride, coords_are_cartesian=True)
        
        # # Get the coordination of each electron in the system
        # electrides_coordination = []
        # new_electride_sites = empty_structure.indices_from_symbol("He")
        # for site_index in new_electride_sites:
        #     electrides_coordination.append(cnn.get_cn(empty_structure, n=site_index))
            
        # return empty_structure, electrides_coordination
        
        
        
            
            
            
        