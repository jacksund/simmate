#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar 22 21:43:11 2023

@author: WarrenLab
"""

import itertools
import math
import time
import warnings
from pathlib import Path

import dask.dataframe as dd
import numpy as np
import pandas as pd
import psutil
from dask.distributed import Client, LocalCluster
from pymatgen.io.vasp import Potcar
from simmate.engine import Workflow
from simmate.toolkit import Structure

from simmate.apps.warrenapp.badelf_tools.utilities import get_electride_num

from simmate.apps.warrenapp.badelf_tools.badelf_algorithm_functions import (
    check_closest_neighbor_for_same_type,
    check_structure_for_covalency,
    get_neighbors_set,
    get_closest_neighbors,
    get_charge_density_grid,
    regrid_numpy_array,
    get_electride_sites,
    get_lattice,
    get_max_voxel_dist,
    get_number_of_partitions,
    # get_partitioning_fine,
    get_partitioning_grid,
    get_partitioning_rough,
    get_real_from_frac,
    get_voxels_site_dask,
    get_voxels_site_multi_plane,
    get_voxels_site_nearest,
    get_voxels_site_volume_ratio_dask,
    write_atom_chgcar,
    write_atom_elfcar,
)

from rich.console import Console
console = Console()

###############################################################################
# Now that we have functions defined, it's time to define the main workflow
###############################################################################


class BadElfAnalysis__Warren__BadelfIonicRadii(Workflow):
    use_database = False

    @classmethod
    def run_config(
        cls,
        directory: Path = None,
        structure_file: str = "POSCAR",
        empty_structure_file: str = "POSCAR_empty",
        partition_file: str = "ELFCAR",
        empty_partition_file: str = "ELFCAR_empty",
        charge_file: str = "CHGCAR",
        valence_file: str = "POTCAR",
        print_atom_voxels: bool = False,
        algorithm: str = "badelf", # other option is voronelf
        check_covalency: bool = True,
        **kwargs,
    ):
        t0 = time.time()
        console.print(f"\nBeginning {algorithm} analysis :goblin:", style="bold green")
        structure = Structure.from_file(directory / structure_file)

        # read in lattice and structure with and without electride sites
        lattice = get_lattice(partition_file=directory / partition_file)
        # try:
        empty_lattice = get_lattice(directory / empty_partition_file)
        empty_structure = Structure.from_file(directory / empty_structure_file)
        # except:
        #     print("No ELFCAR_empty found. Continuing with no electride sites.")
        #     empty_lattice = lattice
        #     empty_structure = structure.copy()
        
        # if the algorithm is voronelf, we treat the structure with electride
        # sites as the main structure. We will skip the step where electride
        # sites found by the Henkelman algorithm are read in
        # if algorithm == "voronelf":
        #     structure, lattice = empty_structure.copy(), empty_lattice.copy()
            
            
            
        # get dictionary of sites and closest neighbors. This always throws
        # the same warning about He's EN so we suppress that here
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            neighbors = get_neighbors_set(structure=structure)
            closest_neighbors = get_closest_neighbors(empty_structure)

        # When using the badelf algorithm, we want to assign electride voxels 
        # based on the zero-flux method, then assign the remaining voxels 
        # using the voronelf method. If we are using the voronelf method, we don't
        # use any zero-flux and need to disable anything based on this.
        if algorithm == "badelf":
            electride_sites = get_electride_sites(empty_lattice)
        elif algorithm == "voronelf":
            electride_sites = []
            
        # we also want the voxel resolution
        voxel_resolution = np.prod(lattice["grid_size"]) / lattice["volume"]
        console.print(f"Voxel Resolution: {round(voxel_resolution, 2)}", style="green")

        # read in partition grid
        if "ELFCAR" in partition_file:
            grid = get_partitioning_grid(
                partition_file=directory / partition_file, lattice=lattice
            )
        elif "CHGCAR" in partition_file:
            grid = get_charge_density_grid(
                charge_file=directory / partition_file, lattice=lattice
            )
        
        # We now check for any covalency that may be in the structure.
        # !!! the current version of BadELF does not have a method for handling
        # covalency. This will hopefully be updated in the future
        if check_covalency:
            check_closest_neighbor_for_same_type(closest_neighbors, empty_structure)
            check_structure_for_covalency(closest_neighbors, grid, empty_lattice, empty_structure)
        
        # regrid the partitioning grid to a higher voxel resolution. This means
        # that high quality interpolation of the grid data only has to happen once.
        # This should speed up the process of partitioning
        if voxel_resolution < 130000:
            console.print("Increasing voxel resolution :chart_increasing:", 
                  style = "green")
            new_grid, regrid_lattice = regrid_numpy_array(lattice, grid)
        else:
            regrid_lattice = lattice.copy()
            new_grid = grid.copy()
        
        new_voxel_resolution = np.prod(regrid_lattice["grid_size"]) / regrid_lattice["volume"]
        console.print(f"New Voxel Resolution: {round(new_voxel_resolution, 2)}",
              style = "green")

        # !!! BadELF alg seems to converge around 10,000-20,000 voxels/A^3. I
        # can probably decrease voxel grids larger than this to speed up the
        # algorithm

        
        # The algorithm now looks at each site-neighbor pair.
        # Along the bond between the pair, we look at ELF values.
        # We find the position of the minimum ELF value.
        # We then find the plane that passes through this minimum and
        # that is perpendicular to the bond between the pair.

        # if new_voxel_resolution > 130000:
        console.print("\nBeginning Partitioning",
              style = "bold green")
        results = get_partitioning_rough(
            neighbors=neighbors,
            lattice=regrid_lattice,
            grid=new_grid,
            rough_partitioning=True,
            structure=structure,
        )
        # else:
        #     rough_partition_results = get_partitioning_rough(
        #         neighbors=neighbors,
        #         lattice=regrid_lattice,
        #         grid=grid,
        #     )
        #     results = get_partitioning_fine(rough_partition_results, grid, regrid_lattice)
        t1 = time.time()

        console.print(f"Partitioning completed in {round(t1-t0,2)} seconds.", style = "green")
        console.print("""
Beginning Voxel Assignment
                      """,
              style = "bold green")
        
        # Now that we've identified the planes that divide the ELF, we now need to
        # actually apply that knowledge, voxel by voxel.

        # For each neighbor of a site, we have a bounding plane.  Only those voxels
        # that are within all bounding planes of a site belong to that site.

        # I go across the elf grid voxel-by-voxel.
        # For each voxel, I get its real space position.
        # I then test if it is within the planes in each site.
        # Only when it matches all the planes do I record it as belonging to a site.

        # !!!!!!!!
        # In this iteration, I'm going to try and treat voxels that may intersect
        # 1 or more planes more rigorously
        #!!!!!!!!!

        # The output, then, is a list of voxels (x,y,z position) that belong
        # to each site.

        # Then, this list of voxels is applied to the total charge density to
        # add up all the incremental charge.

        # create dictionaries for each site's coordinates, charge, min-distance
        # to the surface, and total volume. These will be used to create a
        # summary folder later

        results_coords = {}
        results_charge = {}
        results_min_dist = {}
        results_volume = {}
        # fill site coords dictionary
        for site, site_coord in enumerate(empty_lattice["coords"]):
            results_coords[site] = get_real_from_frac(
                frac_pos=site_coord, lattice=lattice
            )
            # fill min_dist dictionary using the smallest partitioning radius
            if site not in electride_sites:
                radii = []
                for neighbor in results[site].values():
                    radii.append(neighbor["radius"])
                min_radii = min(radii)
                results_min_dist[site] = min_radii
            elif site in electride_sites:
                results_min_dist[site] = 0
            # create empty dictionary for other results that haven't been found yet
            results_charge[site] = float(0)
            results_volume[site] = float(0)

        # read in charge density file
        # make sure this file has same number of atoms as elfcar
        chg = get_charge_density_grid(
            charge_file=directory / charge_file,
            lattice=lattice,
        )
        
        # !!! BadELF converges around 10,000-15,000 voxels/A^3. I should regrid the
        # chg grid here. I should also regrid the incoming electride files if
        # I do this. For now, I'll just do this if we're using the Voronoi method
        # !!! This may not work unless I can make sure everything adds up the
        # same as before. normalizing might be what's causing this problem.
        if algorithm == "voronelf" and voxel_resolution > 20000:
            chg, lattice = regrid_numpy_array(
                lattice, 
                chg, 
                desired_resolution=15000,
                )
            
        # we'll need the volume of each voxel later to calculate the atomic
        # volumes for our output file
        voxel_volume = lattice["volume"] / np.prod(lattice["grid_size"])
        
        # We will also need to find the maximum distance the center of a voxel
        # can be from a plane and still be intersected by it. That way we can
        # handle voxels near partitioning planes with more accuracy
        max_voxel_dist = get_max_voxel_dist(lattice)
        
        
        # We need to get the charge on each electride site and get the coordinates that
        # belong to the electride. We first get a dataframe that indexes all of the
        # coordinates. We'll remove the electride coordinates from this later.
        a, b, c = lattice["grid_size"]

        # Create lists that contain the coordinates of each voxel and their charges
        voxel_coords = [idx for idx in itertools.product(range(a), range(b), range(c))]
        voxel_charges = [float(chg[idx[0], idx[1], idx[2]]) for idx in voxel_coords]

        # Create a dataframe that has each coordinate index and the charge as columns
        # Later we'll remove voxels that belong to electrides from this dataframe
        all_charge_coords = pd.DataFrame(voxel_coords, columns=["x", "y", "z"]).add(1)

        all_charge_coords["chg"] = voxel_charges
        all_charge_coords["site"] = None
        #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        # Now iterate through the charge density coordinates for each electride.
        # This only does something for the BadELF algorithm not the Vornoi one
        for electride in electride_sites:
            # Pull in electride charge density from bader output file (BvAt####.dat format)
            electride_chg = get_charge_density_grid(
                charge_file=directory / f"BvAt{str(electride+1).zfill(4)}.dat",
                lattice=empty_lattice,
            )
            electride_chg, _ = regrid_numpy_array(empty_lattice, electride_chg)
            electride_indices = []
            # For each voxel, check if the electride charge density file has any
            # charge. If it does add its index to the electride_indices list
            for count, idx in enumerate(voxel_coords):
                charge_density = float(electride_chg[idx[0], idx[1], idx[2]])
                if charge_density != 0:
                    # get indices of electride sites
                    electride_indices.append(count)
                    # results_charge[electride] += charge_density
            # add electride site to "site" column for every electride indice
            all_charge_coords.iloc[electride_indices, 4] = electride

        # get the permuations of possible shifts for each voxel.
        permutations = [
            (t, u, v)
            for t, u, v in itertools.product([-a, 0, a], [-b, 0, b], [-c, 0, c])
        ]
        # sort permutations. There may be a better way of sorting them. I
        # noticed that generally the correct site was found most commonly
        # for the original site and generally was found at permutations that
        # were either all negative/0 or positive/0
        permutations_sorted = []
        for item in permutations:
            if all(val <= 0 for val in item):
                permutations_sorted.append(item)
            elif all(val >= 0 for val in item):
                permutations_sorted.append(item)
        for item in permutations:
            if item not in permutations_sorted:
                permutations_sorted.append(item)
        permutations_sorted.insert(0, permutations_sorted.pop(7))

        # We want to open a local dask cluster with appropriate settings. I've
        # done some light testing and found that 1 thread per worker, 2GB mem,
        # and partition sizes of 128,000 voxel coords seems reasonable.
        # For smaller systems (<128,000) it was still benefitial to parallelize
        # though less efficient

        # Get the total number of cpus available and memory available
        cpu_count = math.floor(len(psutil.Process().cpu_affinity()) / 2)
        memory_gb = psutil.virtual_memory()[1] / (1e9)
        # Each worker needs at least 2GB of memory. We select either the number
        # of workers that could have at least this much memory or the number
        # of cores/threads, whichever is smaller
        nworkers = min(math.floor(memory_gb / 2), cpu_count)
        
        console.print(
            """
            Opening local Dask cluster
            """,
            style="bold green"
            )
        with LocalCluster(
            n_workers=nworkers,
            threads_per_worker=2,
            memory_limit="auto",
            processes=True,
        ) as cluster, Client(cluster) as client:
            # put list of indices in dask dataframe. Partition with the same
            # number of partitions as workers
            npartitions = get_number_of_partitions(
                df=all_charge_coords, nworkers=nworkers
            )
            ddf = dd.from_pandas(
                all_charge_coords,
                npartitions=npartitions,
            )

            # site search for all voxel positions.
            ddf["site"] = ddf.map_partitions(
                get_voxels_site_dask,
                results=results,
                permutations=permutations,
                lattice=lattice,
                electride_sites=electride_sites,
                max_distance=max_voxel_dist,
            )
            # run site search and save as pandas dataframe
            pdf = ddf.compute()

            #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            # I've made it so that if a voxel is found to have multiple sites at
            # one transformation it will be stored as -1 in the pdf and if it is
            # found to have multiple sites at more than one transformation it will
            # return -2. The -1 takes priority over -2 as I view it as a more
            # serious issue because I know it should never be possible. Here I
            # need to sort these out and count them before I move on.
            # Count the number of instances where this occurs
            try:
                multi_site_same_trans = pdf["site"].value_counts()[-1]
                multi_site_trans = pdf["site"].value_counts()[-2]
            except:
                multi_site_same_trans = 0
                multi_site_trans = 0
            # I'm going to save these values towards the end of this script in
            # as a file with a csv format.
            # if multi_site_same_trans != 0 or multi_site_trans != 0:
            #     with open(directory / "same_site_voxel_count.txt", "w") as file:
            #         file.write(f"{np.prod(lattice['grid_size'])}\n{multi_site_same_trans}\n{multi_site_trans}")
            # Replace all instances with numpy nan object so that the rest of the
            # alg doesn't break.
            pdf["site"].replace([-1, -2], np.nan, inplace=True)
            #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

            # Group the results by site. Sum the charges and count the total number
            # of voxels for each site. Apply charges and volumes to dictionaries.
            pdf_grouped = pdf.groupby(by="site")
            pdf_grouped_charge = pdf_grouped["chg"].sum()
            pdf_grouped_voxels = pdf_grouped["site"].size()
            for site in results_charge:
                results_charge[site] = pdf_grouped_charge[site]
                results_volume[site] = pdf_grouped_voxels[site] * voxel_volume
            # if printed voxels are requested, update all_coords dataframe
            # if print_atom_voxels:
            all_charge_coords["site"] = pdf["site"]
            # some of the voxels will not return a site. For these we need to check the
            # nearby voxels to see which site is the most common and assign them to that
            # site. To do this we essentially repeat the previous several steps but with
            # the new site searching method.

            # find where the site search returned None
            near_plane_index = np.where(pdf["site"].isnull())
            # We need to convert Nan in pdf to None type objects for when we are
            # iterating through them later
            pdf = pdf.replace({np.nan: None})
            # create new pandas dataframe only containing voxels with no site
            near_plane_pdf = pdf.iloc[near_plane_index].drop(columns=["site"])
            # get a reasonable number of partitions for the near_plane dataframe. This
            # takes slightly more memory than the regular index finder so we increase
            # the number of partition.

            near_plane_npartitions = get_number_of_partitions(
                df=near_plane_pdf, nworkers=nworkers
            )

            # switch from pandas dataframe to partitioned dask dataframe
            near_plane_ddf = dd.from_pandas(
                near_plane_pdf,
                npartitions=near_plane_npartitions,
            )
            # assign function to search for nearby voxels accross dask partitions
            near_plane_ddf["site"] = near_plane_ddf.map_partitions(
                get_voxels_site_volume_ratio_dask,
                lattice=lattice,
                results=results,
                permutations=permutations,
                voxel_volume=voxel_volume,
            )

            # compute and return to pandas
            near_plane_pdf = near_plane_ddf.compute()

        #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        # I've made it so that if some vertices are found to fit with multiple
        # sites, it adds an additional site labeled as -1, -2, or -3.
        # This way I can count how many of them are doing this while still allowing
        # them to be treated as not belonging to any site.
        
        # Define counts for sites with this issue
        vert_multi_site_same_trans = 0
        vert_multi_site = 0
        multi_site_no_plane = 0
        # Check each voxel near a plane
        for row in near_plane_pdf.iterrows():
            try:
                # Check each voxels site assignment (stored in row[1][4]). If
                # -1, the vertices of the voxel were found to potentially belong
                # to multiple sites even at the same transformation. If -2, they
                # were found to potentially belong to multiple sites at different
                # transformations. If -3, the vertices were found to have different
                # sites, but no plane was found to intersect the voxel.
                for site in row[1][4]:
                    if site == -1:
                        vert_multi_site_same_trans += 1
                        continue
                    elif site == -2:
                        vert_multi_site += 1
                        continue
                    elif site == -3:
                        multi_site_no_plane += 1
                        continue
                    # for each site, multiply the fraction of the site times the charge
                    results_charge[site] += row[1][4][site] * row[1][3]
                    results_volume[site] += row[1][4][site] * voxel_volume
                # If print_atom_voxels is requested, add the highest fraction
                # site to all_charge_coords
                # if print_atom_voxels:
                sites = row[1][4]
                max_site_frac = max(sites.values())
                max_site = list(sites.keys())[
                    list(sites.values()).index(max_site_frac)
                ]
                all_charge_coords.loc[row[0], "site"] = max_site
            except:
                # If none of the above is true, there is some other issue with
                # this voxel. For now we are just going to pass it, but in the
                # future, we really shouldn't have any of these assignments. My
                # guess is that each of these issues (-1,-2,-3, except) are related
                # to improper plane assignment that isn't rigorous enough.
                # if row[1][4] is not None:
                #     print(f"{row[1][4]}")
                pass
        # Some sites will be returned as none because they are being split
        # by more than one bordering plane. We handle these with less accuracy
        multi_plane_index = np.where(near_plane_pdf["site"].isnull())
        # We need to convert Nan in pdf to None type objects for when we are
        # iterating through them later
        near_plane_pdf = near_plane_pdf.replace({np.nan: None})
        # create new pandas dataframe only containing voxels with no site
        multi_plane_pdf = near_plane_pdf.iloc[multi_plane_index].drop(columns=["site"])

        if len(multi_plane_pdf) > 0:
            multi_plane_pdf["sites"] = multi_plane_pdf.apply(
                lambda x: get_voxels_site_multi_plane(
                    x["x"],
                    x["y"],
                    x["z"],
                    pdf=pdf,
                    near_plane_pdf=near_plane_pdf,
                    lattice=lattice,
                    electride_sites=electride_sites,
                    results=results,
                ),
                axis=1,
            )
            for row in multi_plane_pdf.iterrows():
                for site in row[1][4]:
                    results_charge[site] += row[1][4][site] * row[1][3]
                    results_volume[site] += row[1][4][site] * voxel_volume
                # if print_atom_voxels:
                    # If no sites are found, using the max function will throw
                    # an error. I just skip these instances here.
                try:
                    sites = row[1][4]
                    max_site_frac = max(sites.values())
                    max_site = list(sites.keys())[
                        list(sites.values()).index(max_site_frac)
                    ]
                    all_charge_coords.loc[row[0], "site"] = max_site
                except:
                    continue
        else:
            # print("no voxels intercepted by more than one plane")
            pass

        # After all other parts have run, sometimes the algorithm still has some
        # voxels that are unassigned. The easiest way to handle these is to give
        # them to the closest atom.
        # get dataframe of all missing voxels
        missing_voxel_index = np.where(multi_plane_pdf["sites"] == {})
        multi_plane_pdf = multi_plane_pdf.replace({np.nan: None})
        missing_voxel_pdf = multi_plane_pdf.iloc[missing_voxel_index].drop(
            columns=["sites"]
        )
        if len(missing_voxel_pdf) > 0:
            perc_voxels = (len(missing_voxel_pdf) / np.prod(lattice["grid_size"])) * 100
            console.print(
                f"""{perc_voxels}% of voxels could not be assigned by the base
            algorithm. Remaining voxels will be assigned by closest atom. 
                  """,
                  style = "bold red"
            )

            missing_voxel_pdf["sites"] = missing_voxel_pdf.apply(
                lambda x: get_voxels_site_nearest(
                    x["x"],
                    x["y"],
                    x["z"],
                    permutations=permutations,
                    lattice=lattice,
                ),
                axis=1,
            )
            # Group the results by site. Sum the charges and count the total number
            # of voxels for each site. Apply charges and volumes to dictionaries.
            missing_voxel_pdf_grouped = missing_voxel_pdf.groupby(by="sites")
            missing_voxel_pdf_grouped_charge = missing_voxel_pdf_grouped["chg"].sum()
            missing_voxel_pdf_grouped_voxels = missing_voxel_pdf_grouped["sites"].size()
            for site in results_charge:
                if site in missing_voxel_pdf_grouped_charge.index.to_list():
                    results_charge[site] += missing_voxel_pdf_grouped_charge[site]
                    results_volume[site] += (
                        missing_voxel_pdf_grouped_voxels[site] * voxel_volume
                    )

            if print_atom_voxels:
                for row in missing_voxel_pdf.iterrows():
                    site = row[1]["sites"]
                    all_charge_coords.loc[row[0], "site"] = site
        else:
            console.print("All voxels assigned",
                  style = "green")
        
        t2 = time.time()
        console.print(f"Total Time: {t2-t0}", style = "green")
        # divide charge by volume to get true charge
        # this is a vasp convention
        for site, charge in results_charge.items():
            results_charge[site] = charge / (a * b * c)
        nelectrons = sum(results_charge.values())

        #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        # Now I need to save the number of problem voxels in a report document.
        # I think it would be most useful to do this in a csv style format so
        # that I can easily take in the data later. I'm going to save all of the
        # problems for every situation. The columns will be as follows:
        # formula, spacegroup label, directory, total voxel count
        # voxel centers at same transformation, voxel centers at different transformations,
        # voxel vertices at same transformation, voxel vertices at different transfromations,
        # voxels with multiple sites at vertices but no plane intersection.
        # All of these except the last group refer to voxels with issues related
        # to being assigned to more than one site. This is a bigger issue for
        # the sites, and may be normal for the vertices if they are split by a
        # plane.
        with open(directory / "same_site_voxel_count.txt", "w") as file:
            file.write(
                f"{structure.formula},{structure.get_space_group_info()[0]},{str(directory.absolute())},{np.prod(lattice['grid_size'])},{multi_site_same_trans},{multi_site_trans},{vert_multi_site_same_trans},{vert_multi_site},{multi_site_no_plane}"
            )
        #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

        #######################################################################
        # Print atom voxels
        #######################################################################
      
        if print_atom_voxels:
            # iterate over each element in the empty lattice
            console.print("Writing atom CHGCARs and ELFCARs",
                  style = "green")
            for element in empty_lattice["elements"]:
                # write each atom/electride type to a CHGCAR/ELFCAR type file
                write_atom_chgcar(directory, lattice, all_charge_coords, empty_structure, element)
                write_atom_elfcar(directory, lattice, all_charge_coords, grid, empty_structure, element)
            # The topology algorithm works by looking along lines in the ELF from
            # one electride to the next. We need to pass the voxels belonging to
            # electride sites on to this workflow by saving the information to a
            # single file. We do this regardless of if the user requests the
            # other voxels be printed
        else:
            console.print("Writing electride ELFCAR",
                  style = "green")
            for element in empty_lattice["elements"]:
                # We only want electrides (noted with an He) so we skip everything
                # else here.
                if element != "He":
                    continue
                write_atom_elfcar(directory, lattice, all_charge_coords, grid, empty_structure, element)
        
        console.print(f"{algorithm} analysis completed :party_popper:", style="bold blue")
        ###############################################################################
        # Save information into a dictionary that will be saved to a database.
        ###############################################################################

        # load the electron counts from the POTCAR. Here I ignore a warning
        # from pymatgen that often gets thrown if they don't recognize a given
        # pseudopotential.
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            potcars = Potcar.from_file(directory / valence_file)
        nelectron_data = {}
        # the result is a list because there can be multiple element potcars
        # in the file (e.g. for NaCl, POTCAR = POTCAR_Na + POTCAR_Cl)
        for potcar in potcars:
            nelectron_data.update({potcar.element: potcar.nelectrons})
            
        # create lists to store the element list, oxidation states, charges,
        # minimum distances, and atomic volumes
        elements = []
        oxi_state_data = []
        charge_data = []
        min_dists = []
        atomic_volumes = []
        # iterate over the charge results and add the results to each list
        for site_index, site_charge in results_charge.items():
            # get structure site
            site = empty_structure[site_index]
            # get element name
            element_str = site.specie.name
            # Change electride dummy atom name to e
            if element_str == "He":
                element_str = "e"
            # add element to element list
            elements.append(element_str)
            # calculate oxidation state and add it to the oxidation state list
            if element_str == "e":
                oxi_state = -site_charge
            else:
                oxi_state = nelectron_data[element_str] - site_charge
            oxi_state_data.append(oxi_state)
            # add the corresponding charge, distance, and atomic volume to the
            # respective lits
            charge_data.append(site_charge)
            min_dists.append(results_min_dist[site_index])
            atomic_volumes.append(results_volume[site_index])
            
        # Calculate the "vacuum charge" or the charge not associated with any atom.
        # Idealy this should be 0
        total_electrons = sum(nelectron_data.values())
        vacuum_charge = round((total_electrons - nelectrons),6)
        
        # Calculate the "vacuum volume" or the volume not associated with any atom.
        # Idealy this should be 0
        vacuum_volume = round((lattice["volume"] - sum(results_volume.values())),6)
        
        # get the number of electride sites.
        nelectrides = get_electride_num(directory, empty_structure)
        
        results_dataframe = {
                "oxidation_states": oxi_state_data,
                "algorithm": algorithm,
                "charges": charge_data,
                "min_dists": min_dists,
                "atomic_volumes": atomic_volumes,
                "element_list": elements,
                "vacuum_charge": vacuum_charge,
                "vacuum_volume": vacuum_volume,
                "nelectrons": nelectrons,
                "nelectrides": nelectrides, 
            }
        return results_dataframe