# -*- coding: utf-8 -*-
from pathlib import Path

import numpy as np
from pymatgen.io.vasp import Poscar, Elfcar, Chgcar
from simmate.toolkit import Structure

from simmate.apps.warrenapp.badelf_tools.badelf_algorithm_functions import (
    get_closest_neighbors,
    get_lattice,
    get_line_frac_min_rough,
    get_partitioning_grid,
    get_partitioning_line,
    get_position_from_min,
    get_real_from_vox,
    get_voxel_from_index,
    get_voxel_from_neigh_CrystalNN,
)


def check_required_files(directory: Path, required_files: list):
    """
    Checks to make sure that all the files in a folder exist. Otherwise raises
    an error.
    """
    if not all((directory / file).exists() for file in required_files):
        raise Exception(
            f"""Make sure your `setup` method directory source is defined correctly. 
        The following files must exist in the directory where 
        this task is ran but some are missing: {required_files}"""
        )
        
def check_chgcar_elfcar_grids(directory):
    
    check_required_files(directory, ["ELFCAR", "CHGCAR"])
    chgcar_lattice = get_lattice("CHGCAR")
    elfcar_lattice = get_lattice("ELFCAR")
    
    if chgcar_lattice["grid_size"] == elfcar_lattice["grid_size"]:
        return True, chgcar_lattice["grid_size"]
    else:
        return False, chgcar_lattice["grid_size"]


def get_badelf_radius(neigh: list, lattice: dict, site_pos: dict, grid):
    """
    Function for getting the line, plane, and other information between a site
    and neighbor
    """

    # get voxel of neighbor from cns neighbor dict
    neigh_pos = get_voxel_from_neigh_CrystalNN(neigh, lattice)
    real_site_pos = get_real_from_vox(site_pos, lattice)
    # we need a straight line between these two points.  get list of all ELF values
    elf_pos, elf_values = get_partitioning_line(site_pos, neigh_pos, grid)
    # smooth the line

    # find the minimum position and value along the elf_line
    # the first element is the fractional position, measured from site_pos
    min_elf = get_line_frac_min_rough(elf_values, rough_partitioning=True)

    # convert the minimum in the ELF back into a position in the voxel grid
    min_pos_vox = get_position_from_min(min_elf[2], site_pos, neigh_pos)

    """ a point and normal vector describe a plane
    a(x-x1) + b(y-y1) + c(z-z1) = 0 
    a,b,c is the normal vecotr, x1,y1,z1 is the point
    """
    # convert this voxel grid_pos back into the real_space
    real_vox_pos = get_real_from_vox(min_pos_vox, lattice)
    # get the plane perpendicular to the position.

    # it is also helpful to know the distance of the minimum from the site
    radius = sum([(b - a) ** 2 for a, b in zip(real_site_pos, real_vox_pos)]) ** (0.5)
    return radius


# chagned
def get_max_radius(structure: Structure, partition_file: str):
    """
    Function for partitioning the grid. Looks along a 1D line between each
    site and its closest and second closest neighbors. Finds the minimum
    along that line and creates a perpindicular plane. Returns a nested dictionary
    that goes: dict of sites > dict of each site/neighbor pair > dict of line
    and plane data.
    """
    closest_neighbors = get_closest_neighbors(structure)
    lattice = get_lattice(partition_file)
    grid = get_partitioning_grid(partition_file, lattice)
    site_radii = {}
    element_radii = {}
    # iterate through each site in the structure
    for site, neighs in closest_neighbors.items():
        # create key for each site
        site_radii[site] = {}
        # get voxel position from fractional site.
        site_pos = get_voxel_from_index(site, lattice)
        # We want to get the radius based on bonds to closest neighbors. This
        # is stored in our closest neighbors dictionary as the first neighbor
        # site, neigh[0] for each site.
        # In some structures (ex. Y12H4) an atoms closest neighbor is another
        # of the same type of atom. This doesn't contain any useful information
        # about an ionic radius because this bond should be highly covalent
        # We prevent the inclusion of these radii by comparing the site and
        # neighbor elements.
        site_element = structure.species[site].name
        neigh_element = structure.species[neighs[0]["site_index"]].name
        if site_element == neigh_element:
            site_radii[site] = 0
        else:
            site_radii[site] = get_badelf_radius(neighs[0], lattice, site_pos, grid)
    for element in structure.composition.elements:
        radii = []
        for site in structure.indices_from_symbol(element.name):
            radii.append(site_radii[site])
        element_radii[element.name] = max(radii)
    # In the case where all atoms of one type are closest to atoms of the same
    # type, we will not find any radius. In these cases we return an exception
    # as the rest of the work will fail.
    if element_radii != 0:
        return element_radii
    elif element_radii == 0:
        raise Exception(
            """BadELF radius search failed. Make sure you are not looking at
            a material with fully covalent atoms (i.e. all atoms closest 
            neighbors are the same atom).
            """
        )


def get_empties_from_bcf(
    directory: Path,
    structure: Structure,
    min_charge: float = 0.15,
):
    """
    Checks the BCF.dat output file from the Henkelman algorithm for charge
    maxima that are far from other atoms with large charges, and adds in "dummy"
    atoms at these sites. Returns a Structure object.
    """
    # Set the correct density file (CHGCAR or ELFCAR) to update depending on
    # if analysis_type is badelf or bader

    required_files = ["ELFCAR", "POSCAR", "BCF.dat"]

    # Check that all of the required files are present
    try: check_required_files(directory=directory, required_files=required_files)
    except: 
        raise Exception(
            f"""
            One or more of the following required files is missing.
            files: {required_files}.
            directory: {directory}
            If the BCF.dat is missing, make sure that your VASP settings result
            in an ELFCAR and GHGCAR with the same grid size.
            """
            )

    # We want to compare each ELF maximum to each atom and determine if it is
    # within that atoms "badelf radius" which is the distance between an atom
    # and the minimum between it and its closest neighbor. This is easily done
    # using pymatgen's get_distance method which allows us to find the atoms
    # closest to each electride site

    # get the badelf radii
    element_radii = get_max_radius(structure, directory / "ELFCAR")

    # Pull coordinates of bader density peaks from BCF.dat
    bcf = np.genfromtxt(
        fname=(directory / "BCF.dat"),
        dtype=float,
        skip_header=2,
        skip_footer=1,
    )

    # convert the new bcf coordinates to a list to easily add to a Structure
    bcf_coords = np.delete(bcf, [0, 4, 5, 6], axis=1).tolist()

    # copy the original structure and add all of the coordinates of the maxima
    # in our bcf array.
    structure_with_charges = structure.copy()
    for coord in bcf_coords:
        structure_with_charges.append("H", coord, coords_are_cartesian=True)

    # save the number of atoms in the original structure
    number_of_atoms = len(structure.sites)

    # Create an empy list that we will populate with array's of potential electride
    # positions
    empty_sites = []

    # iterate through only the bcf charge peaks in the new structure that we
    # created.
    for i in range(number_of_atoms, number_of_atoms + len(bcf_coords)):
        # create a tag for if this is an electride site
        electride_site = True
        # we have radii for each element in the structure. we want to make sure
        # the site is outside the range for each element's radius. iterate
        # through each element
        for element in structure.composition.elements:
            # create a list for the distances between charge site and the atoms
            closest_dist = []
            # iterate through the atoms and if they are the correct element,
            # add the distance to our distance list. Take the minimum of these
            # as the distance to the nearest atom to the site. Also grab the
            # charge for this site from the bcf.
            for j in range(number_of_atoms):
                if structure.species[j] == element:
                    closest_dist.append(structure_with_charges.get_distance(i, j))
            dist = min(closest_dist)
            charge = bcf[(i - number_of_atoms), 4]
            # if our distance is less than the atomic radius or the minimum
            # charge we set, don't consider this site an electride.
            if dist < element_radii[element.name] or charge < min_charge:
                electride_site = False
                break
        # If after comparing to all atoms the electride tag is still true, we
        # add this to our list of electrides.
        if electride_site == True:
            empty_sites.append(structure_with_charges.sites[i].coords)

    # Append an "empty" He atom to our structure for the bader analysis to associate
    # electron charge with. The coordinates in the BCF.dat file are cartesian so
    # we include this tag
    structure_empty = structure.copy()
    # sites_to_remove = []
    for charge_site in empty_sites:
        structure_empty.append(
            species="He", coords=charge_site, coords_are_cartesian=True
        )

    # Sometimes the program finds two electride sites that are right next to
    # eachother(maybe due to voxelation?). To account for this, we check through
    # all of the sites in our structure and remove any that are close to eachother
    # (within 0.3 angstrom. This is arbitrary and may need to be updated)
    sites_to_remove = []
    for site_index in range(len((structure_empty.sites))):
        for other_site_index in range(site_index + 1, len(structure_empty.sites)):
            if structure_empty.get_distance(site_index, other_site_index) < 0.3:
                sites_to_remove.append(site_index)
    structure_empty.remove_sites(sites_to_remove)
    
    return structure_empty


# This function writes a file POSCAR_empty which contains the original structure
# information from the POSCAR with the added lines for electride sites.
def write_poscar_empty(directory: Path, structure_empty: Structure):
    """
    Writes a structure to a file called POSCAR_empty. Intended to be used
    with a Structure object containing empty atoms at electride sites.
    """
    poscar_empty = Poscar(structure=structure_empty).get_string().split("\n")
    poscar_empty_corrected = []
    for i, line in enumerate(poscar_empty):
        if i < 5:
            poscar_empty_corrected.append(line + "\n")
        elif i == 5:
            poscar_empty_corrected.append("   " + line.replace(" ", "    ") + " \n")
        elif i == 6:
            poscar_empty_corrected.append(
                "     " + line.strip().replace(" ", "     ") + "\n"
            )
        elif i == 7:
            poscar_empty_corrected.append("Direct\n")
        elif i > 7:
            site = line.split(" ")
            site.pop(-1)
            adjusted_line = ""
            for coordinate in site:
                try:
                    coordinate = float(coordinate)
                    coordinate = format(coordinate, ".6f")
                    adjusted_line = adjusted_line + f"  {coordinate}"
                except:
                    pass
            poscar_empty_corrected.append(adjusted_line + "\n")

    with open(directory / "POSCAR_empty", "w") as file:
        file.writelines(poscar_empty_corrected)


def get_electride_num(directory: Path = None, structure: Structure = None):
    """
    A function for getting the total number of electride sites. Used for
    data workup for database entry.
    """
    if structure is None:
        structure = Structure.from_file(directory / "POSCAR_empty")
    
    electride_sites = 0
    # We search for helium atoms which we use as the dummy atoms for electride
    # sites.
    for element in structure.atomic_numbers:
        if element == 2:
            electride_sites += 1
    return electride_sites


def write_density_file_empty(
    directory: Path,
    structure: Structure,
    analysis_type: str = "badelf",
):
    """
    A function for replacing the structure at the beginning of a CHGCAR or
    ELFCAR file and writing new CHGCAR_empty and ELFCAR_empty files. Structure
    must be the original structure without empty atoms and a POSCAR_empty
    file must already exist in the directory.
    """
    # Set names of density files based on analysis_type.
    if analysis_type == "badelf":
        density_files = ["CHGCAR", "ELFCAR"]
    elif analysis_type == "bader":
        density_files = ["CHGCAR", "CHGCAR_sum"]
    elif analysis_type == "both":
        density_files = ["CHGCAR", "CHGCAR_sum", "ELFCAR"]
    # Check for required files
    required_files = density_files + ["POSCAR_empty"]
    check_required_files(directory=directory, required_files=required_files)
    # Get number of lines to replace in teh ELFCAR
    lines_to_replace = structure.num_sites + 8
    # Run for each file
    for density_file in density_files:
        # Open CHGCAR or ELFCAR and add all of the lines past the structure info
        # to a list.
        file = open(directory / f"{density_file}", "r")
        early_lines_to_keep = []
        later_lines_to_keep = []
        for i, line in enumerate(file):
            if i < 5:
                early_lines_to_keep.append(line)
            elif i > lines_to_replace:
                later_lines_to_keep.append(line)
        file.close()
        # Copy over the structure file with empties.
        structure_lines = []
        with open(directory / "POSCAR_empty") as file:
            for i, line in enumerate(file):
                if i > 4:
                    structure_lines.append(line)

        with open(directory / f"{density_file}_empty", "w") as file:
            file.writelines(early_lines_to_keep)
            file.writelines(structure_lines)
            file.writelines(later_lines_to_keep)


def get_density_file_empty(
    directory: Path,
    structure: Structure,
    min_charge: float = 0.45,
    analysis_type: str = "badelf",
):
    """
    Checks the BCF.dat output file from the Henkelman algorithm for charge
    maxima that are far from other atoms with large charges, and adds in "dummy"
    atoms at these sites. This is meant to be used when searching for electrides
    or when working with known electrides. It will return the empty structure
    and number of electrides if any electrides are found.
    """
    # Get a structure object with empty atoms at electride sites
    structure_empty = get_empties_from_bcf(
        directory=directory,
        structure=structure,
        min_charge=min_charge,
    )
    
    # Check if there are any electrides in the empty structure
    electride_num = get_electride_num(directory, structure_empty)
    
    if electride_num > 0 :
        # Write the structure to a POSCAR_empty file. This must be in a specific format.
        # Here we take care of the formatting of lines 6 and on. The early lines
        # are handled in the replace_density_function function
        print("Electride sites detected. Writing files with empty 'dummy' sites")
        write_poscar_empty(directory=directory, structure_empty=structure_empty)
    
        # Replace the ELFCAR and CHGCAR files with empty versions
        write_density_file_empty(
            directory=directory, structure=structure, analysis_type=analysis_type
        )
        return structure_empty, electride_num
    else:
        print("No electrides detected. Continuing with base structure.")
        return None, 0
    
def convert_atom_chgcar_to_elfcar(directory: Path,
                                 chgcar_file: str = "BvAt_summed.dat",
                                 elfcar_file: str = "ELFCAR_empty",
                                 output_file: str = "ELFCAR_e"
                                 ):
    chgcar = Chgcar.from_file(directory / chgcar_file)
    elfcar = Elfcar.from_file(directory / elfcar_file)
    
    chgcar_data = chgcar.data["total"]
    elfcar_data = elfcar.data["total"]
    
    elfcar_data[chgcar_data == 0] = 0
    
    elfcar.data = {"diff": elfcar_data, "total": elfcar_data}
    elfcar.write_file(directory / output_file)
