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
import pandas
import pandas as pd
import psutil
from dask.distributed import Client, LocalCluster
from pymatgen.io.vasp import Chgcar, Elfcar, Poscar
from simmate.engine import Workflow
from simmate.toolkit import Structure

from simmate.apps.warrenapp.badelf_tools.badelf_algorithm_functions import (
    get_50_neighbors,
    get_charge_density_grid,
    get_electride_sites,
    get_lattice,
    get_max_voxel_dist,
    get_number_of_partitions,
    get_partitioning_fine,
    get_partitioning_grid,
    get_partitioning_rough,
    get_real_from_frac,
    get_voxels_site_dask,
    get_voxels_site_multi_plane,
    get_voxels_site_nearest,
    get_voxels_site_volume_ratio_dask,
)
from simmate.apps.warrenapp.models import WarrenPopulationAnalysis

###############################################################################
# Now that we have functions defined, it's time to define the main workflow
###############################################################################


class PopulationAnalysis__Warren__BadelfIonicRadii(Workflow):
    description_doc_short = "BadELF based on ionic radii"

    database_table = WarrenPopulationAnalysis

    @classmethod
    def run_config(
        cls,
        directory: Path = None,
        structure_file: str = "POSCAR",
        partition_file: str = "ELFCAR",
        empty_partition_file: str = "ELFCAR_empty",
        charge_file: str = "CHGCAR",
        print_atom_voxels: bool = False,
        **kwargs,
    ):
        t0 = time.time()
        structure = Structure.from_file(directory / structure_file)
        # get dictionary of sites and closest neighbors. This always throws
        # the same warning about He's EN so we suppress that here
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            neighbors50 = get_50_neighbors(structure=structure)

        # read in lattice with and without electride sites
        lattice = get_lattice(partition_file=directory / partition_file)
        try:
            empty_lattice = get_lattice(directory / empty_partition_file)
        except:
            print("No ELFCAR_empty found. Continuing with no electride sites.")
            empty_lattice = lattice

        # We need to assign electride voxels based on the traditional Bader
        # method, then assign the remaining voxels in the hard-sphere division way.
        # get the indices for electride sites
        electride_sites = get_electride_sites(empty_lattice)

        # we'll need the volume of each voxel later to calculate the atomic
        # volumes for our output file
        voxel_volume = lattice["volume"] / np.prod(lattice["grid_size"])

        # we also want the voxel resolution
        voxel_resolution = np.prod(lattice["grid_size"]) / lattice["volume"]
        print(f"Voxel Resolution: {voxel_resolution}")

        # read in partition grid
        if partition_file == "ELFCAR":
            grid = get_partitioning_grid(
                partition_file=directory / partition_file, lattice=lattice
            )
        elif partition_file == "CHGCAR":
            grid = get_charge_density_grid(
                charge_file=directory / partition_file, lattice=lattice
            )

        # The algorithm now looks at each site-neighbor pair.
        # Along the bond between the pair, we look at ELF values.
        # We find the position of the minimum ELF value.
        # We then find the plane that passes through this minimum and
        # that is perpendicular to the bond between the pair.

        if voxel_resolution > 130000:
            results = get_partitioning_rough(
                neighbors50=neighbors50,
                lattice=lattice,
                grid=grid,
                rough_partitioning=True,
            )
        else:
            rough_partition_results = get_partitioning_rough(
                neighbors50=neighbors50,
                lattice=lattice,
                grid=grid,
            )
            results = get_partitioning_fine(rough_partition_results, grid, lattice)
        t1 = time.time()

        print(f"Partitioning Time: {t1-t0}")
        # We will also need to find the maximum distance the center of a voxel
        # can be from a plane and still be intersected by it. That way we can
        # handle voxels near partitioning planes with more accuracy
        max_voxel_dist = get_max_voxel_dist(lattice)

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

        # We need to get the charge on each electride site and get the coordinates that
        # belong to the electride. We first get a dataframe that indexes all of the
        # coordinates. We'll remove the electride coordinates from this later.

        a, b, c = lattice["grid_size"]

        # Create lists that contain the coordinates of each voxel and their charges

        #!!!!
        # Why did I do this instead of keeping everything in an array so that
        # indexing is easier?
        voxel_coords = [idx for idx in itertools.product(range(a), range(b), range(c))]
        voxel_charges = [float(chg[idx[0], idx[1], idx[2]]) for idx in voxel_coords]

        # Create a dataframe that has each coordinate index and the charge as columns
        # Later we'll remove voxels that belong to electrides from this dataframe
        all_charge_coords = pd.DataFrame(voxel_coords, columns=["x", "y", "z"]).add(1)

        all_charge_coords["chg"] = voxel_charges
        all_charge_coords["site"] = None
        #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        # Now iterate through the charge density coordinates for each electride
        for electride in electride_sites:
            # Pull in electride charge density from bader output file (BvAt####.dat format)
            electride_chg = get_charge_density_grid(
                charge_file=directory / f"BvAt{str(electride+1).zfill(4)}.dat",
                lattice=empty_lattice,
            )
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
            if print_atom_voxels:
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
                if print_atom_voxels:
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
                if print_atom_voxels:
                    # If no sites are found, using the max function will through
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
            print(
                f"""{perc_voxels}% of voxels could not be assigned by the base
            algorithm. Remaining voxels will be assigned by closest atom. 
                  """
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
            print("All voxels assigned.")

        # divide charge by volume to get true charge
        # this is a vasp convention
        for site, charge in results_charge.items():
            results_charge[site] = charge / (a * b * c)
        total_charge = sum(results_charge.values())

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
            # get poscar object
            try:
                poscar = Poscar(Structure.from_file(directory / "POSCAR_empty"))
            except:
                poscar = Poscar(structure)

            # iterate over each element in the empty lattice
            for element in empty_lattice["elements"]:
                # get list of site indices for each type of atom
                site_indices = structure.indices_from_symbol(element)
                # if "dummy" atom, replace string with e
                if element == "He":
                    element = "e"
                # create an empty numpy array for the chgcar and elfcar
                chgcar_data = np.zeros(lattice["grid_size"])
                elfcar_data = np.zeros(lattice["grid_size"])
                # iterate over all voxels and assign elf and charge values
                # to numpy arrays
                for row in all_charge_coords.iterrows():
                    if row[1]["site"] in site_indices:
                        x = int(row[1]["x"] - 1)
                        y = int(row[1]["y"] - 1)
                        z = int(row[1]["z"] - 1)
                        chgcar_data[x][y][z] = row[1]["chg"]
                        elfcar_data[x][y][z] = grid[x][y][z]

                # create elfcar and chgcar objects and write to file
                chgcar_data = {"diff": chgcar_data, "total": chgcar_data}
                elfcar_data = {"diff": elfcar_data, "total": elfcar_data}
                chgcar = Chgcar(poscar, chgcar_data)
                elfcar = Elfcar(poscar, elfcar_data)
                chgcar.write_file(f"CHGCAR_{element}")
                elfcar.write_file(f"ELFCAR_{element}")
        ###############################################################################
        # Save information into ACF.dat like file
        ###############################################################################
        # We need to write a file that's the same format as the Henkelman group's
        # bader output files so that our database records properly. These lines
        # format our output information. It should be noted that our algorithm
        # currently doesn't give vacuum charges, vacuum volumes, or mininum
        # distances to partition surfaces the way that the Henkelman groups does
        acf_lines = []
        acf_lines.extend(
            [
                "    #         X           Y           Z       CHARGE      MIN DIST   ATOMIC VOL\n",
                " --------------------------------------------------------------------------------\n",
            ]
        )
        for site in results_charge:
            line = f"    {site}"
            for coord in results_coords[site]:
                line += "{:>12.6f}".format(coord)
            line += "{:>12.6f}".format(results_charge[site])
            line += "{:>13.6f}".format(results_min_dist[site])
            line += "{:>13.6f}".format(results_volume[site])
            line += "\n"
            acf_lines.append(line)
        acf_lines.extend(
            [
                " --------------------------------------------------------------------------------\n",
                "    VACUUM CHARGE:               0.0000\n",
                "    VACUUM VOLUME:               0.0000\n",
                f"    NUMBER OF ELECTRONS:{format(total_charge,'>15.4f')}\n",
            ]
        )

        with open(directory / "ACF.dat", "w") as file:
            file.writelines(acf_lines)
        t2 = time.time()
        print(f"Time for partitioning: {t1 - t0}")
        print(f"Total time: {t2-t0}")
