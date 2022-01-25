# -*- coding: utf-8 -*-

import numpy

from simmate.toolkit import Structure

from pymatgen.core.lattice import Lattice  # BUG -- this is only for a bug-fix


class Poscar:
    """
    This is format converter class for loading and writing POSCAR or CONTCAR
    files, which are VASP's version of structure files (as oppossed to a cif
    file for example). When you initialize this class, you're only setting generic
    settings. You will either load a POSCAR file by doing...
        my_structure = Poscar.from_file(my_poscar_filename)
    Or you will write a POSCAR file using your Simmate Structure by doing...
        Poscar.write_file(my_structure, my_poscar_filename)
    If you have a ton of files to write, you can do use this method in parallel too...
        Poscar.write_many_files([struct1, struct2, ...], [filename1, filename2, ...])
    """

    @staticmethod
    def from_file(filename="POSCAR", read_velocities=False):
        """
        Reads a Poscar from a file.
        The code will attempt to determine the elements in the POSCAR
        in the following order of priority:
            1. If element symbols are at the end of each coordinate, then this
            is the prefferred method and the most explicit in VASP.
            2. Look for element symbols on the 6th line and match them with the
            nsites on the 7th line. This is 2nd in priority because we do not
            enforce that the structure's sites are sorted in the poscar.
        Args:
            filename (str): File name containing Poscar data.
            read_velocities (bool): Whether to read or not velocities if they
                are present in the POSCAR. Default is True.
        Returns:
            Structure object.
        """
        # open the file, grab the lines, and then close it
        with open(filename) as file:
            lines = file.readlines()

        # Rather than iterate with "for line in lines", POSCAR has a common
        # header where each line has a set piece of information. So I can
        # use this to just look at the first X lines one by one.
        # Remember that python counting starts from 0.

        # the first line is just a comment, so skip it
        # pass lines[0]

        # the 2nd line is a scaling factor for the lattice matrix
        # If the POSCAR was written by Simmate, this value is always 1.0.
        # NOTE -- if this value is negative, it actually represents the total
        # volume for the lattice. I account for this below.
        lattice_scalefactor = float(lines[1])

        # the 3rd, 4th, and 5th lines are the lattice matrix where each line
        # is the a, b, and c lattice vector respectively.
        lattice_matrix = [line.split() for line in lines[2:5]]
        # convert to numpy array of floats
        lattice_matrix = numpy.array(lattice_matrix).astype(float)

        # I still need to scale the entire lattice to the proper size, but again
        # I need to make sure the factor isn't negative, as that would mean
        # it is *not* a scaling factor but the target volume!
        if lattice_scalefactor > 0:
            lattice_matrix *= lattice_scalefactor
        elif lattice_scalefactor < 0:
            # OPTIMIZE -- Should I just make the Structure object first and then
            # scale to the volume, or just do that calculation here?
            vol = abs(numpy.linalg.det(lattice_matrix))
            lattice_matrix *= (-lattice_scalefactor / vol) ** (1 / 3)
        # the else is if the factor is 0, which should never happen

        # The next line contains the elements, such as "Na Cl", and the line
        # after that contains their count such as "1 1". We may not even
        # need to read these lines if elements are specified at the end of each
        # coordinate, but let's do it anyways just in case.
        elements = lines[5].split()
        nelements = [int(value) for value in lines[6].split()]

        # The next line (now on the 8th) has some variance. If it says "Direct"
        # then we have a relatively simple format. If it says "Selective Dynamics",
        # then we have to follow a different formatting template.
        # We will copy what VASP does and only look at the first letter of the line.
        # I make the letterlowercase too to simplify my code below
        format_flag = lines[7].strip()[0].lower()
        # This flag tells us a number of things such as what form the coordinates
        # are in and if there are dynamic tags attached to each coord. Let's check
        # to see what format we are using.
        if format_flag == "s":
            # "s" indicates we are using selective dynamics
            is_selective_dynamics = True
            # it also tells us that the cart vs frac format flag is actually on line 9
            # so we need to reset this value
            format_flag = lines[8].strip()[0].lower()
        else:
            is_selective_dynamics = False
        # now we know which line this info is on, lets see what format we are using.
        # We use if instead of elif, because we still want to enter even if we
        # had format_flag=="s" --> which we then updated!
        if format_flag == "d":
            # "d" stands for "direct" which is fractional coordinates
            is_cart_coords = False
        elif format_flag == "c":
            # "c" stands for "cartesian"
            is_cart_coords = True

        # let's have lists where we load all of the site symbols and coords
        # For example, Ca2N will end up ["Ca", "Ca", "N"]. As a default, we have
        # this list build off of lines 4 and 5. If symbols exist at the end of
        # each coordinate though, this will be overwritten below.
        site_elements = [
            element
            for index, element in enumerate(elements)
            for n in range(nelements[index])
        ]
        site_coords = []
        # let's also have empty lists ready to go for selective dynamics and
        # velocities if we need them.
        selective_dynamics = []
        velocities = []

        # we can now iterate through all of these lines and pull out the
        # coordinates and check for the symbols at the end of each line
        for index, line in enumerate(lines[8:]):

            # if we are reading velocities after this, then we want to keep track
            # of what line we finish up on. The +9 is because that's where
            # we started for this enumeration for-loop.
            current_line_index = index + 9

            # we could have an empty line(s) at the end of the file that
            # trigger us to break from this loop
            if line.startswith("\n"):
                break
            # split this row up into its values
            values = line.split()
            # the first three values are the xyz coordinates
            coordinates = [float(value) for value in values[0:3]]
            # add this to list
            site_coords.append(coordinates)
            # if we have selective dynamics, the next three values are for that
            if is_selective_dynamics:
                # the next three values are for the selective dynamics and they
                # include series of "T" or "F" values for True/False on whether
                # the site can move along a, b, or c respectively.
                dynamic_tags = [
                    True if "T" in value else False for value in values[3:6]
                ]
                selective_dynamics.append(dynamic_tags)

            # check if there's an element symbol at the end of the line. This
            # can be done simply by check the length of it the line
            if not is_selective_dynamics and len(values) == 4:
                # update the element symbol which will correspond to the
                # enumeration index that we are at.
                site_elements[index] = values[3]
            elif is_selective_dynamics and len(values) == 7:
                # update the element symbol which will correspond to the
                # enumeration index that we are at.
                site_elements[index] = values[6]

        # if the sites are cartesian, the lattice scaling factor from above
        # also applies to the coordinates
        # BUG -- pymatgen looks to have this same bug, but what if the
        # scaling factor is negative (i.e. the volume). This will not behave
        # correctly. To fix this, it would actually be easiest to do all
        # scaling after the Structure object is made.
        if is_cart_coords:
            site_coords *= lattice_scalefactor

        # Now lets see if we should read velocities or not from the POSCAR
        if read_velocities:
            # TODO -- this is important for MD simmulations so I should add it.
            # Use this variable that I keep track of above when I actually
            # write this feature
            current_line_index += 1
            raise Exception("Sorry, this isn't supported yet.")

        # if there are selective_dynamics or velocities that we grabbed from above
        # then we should add them to the final structure's site properties
        site_properties = {}
        if selective_dynamics:
            site_properties.update({"selective_dynamics": selective_dynamics})
        if velocities:
            site_properties.update({"velocities": velocities})

        # now lets put everything together and make the Structure object!
        structure = Structure(
            lattice=lattice_matrix,
            species=site_elements,
            coords=site_coords,
            coords_are_cartesian=is_cart_coords,
            site_properties=site_properties,
        )

        # now return the final structure!
        return structure

    @staticmethod
    def to_file(
        structure,
        filename="POSCAR",
        comment=None,
        add_selective_dynamics=False,
        add_velocities=False,
        significant_figures=6,  # !!! how many does VASP ouput? I should use that.
    ):
        """
        Returns a string to be written as a POSCAR file. By default, site
        symbols are written, which means compatibility is for vasp >= 5.
        Args:
            direct (bool): Whether coordinates are output in direct or
                cartesian. Defaults to True.
            vasp4_compatible (bool): Set to True to omit site symbols on 6th
                line to maintain backward vasp 4.x compatibility. Defaults
                to False.
            significant_figures (int): No. of significant figures to
                output all quantities. Defaults to 6. Note that positions are
                output in fixed point, while velocities are output in
                scientific format.
        Returns:
            String representation of POSCAR.
        """

        # POSCAR format can only support ordered structures, so no partial
        # occupancies are allowed. Check the Structure to ensure this.
        if not structure.is_ordered:
            raise ValueError(
                "Structure with partial occupancies cannot be converted into POSCAR!"
            )

        # let's have a list where we keep track of list of lines that we
        # will join at the end
        lines = []

        # first line is just a comment. If the user didn't supply one, I will
        # just use the commpositon, so something like "NaCl"
        lines.append(comment if comment else str(structure.composition))

        # The next line is a scaling factor for the lattice, which is really
        # only useful if you are making a file by hand. We will instead just set
        # the scaling factor to 1.0.
        lines.append("1.0")

        # BUG -- This comment and code is from pymatgen. I wonder if VASP has
        # since fixed this...? Also this will invert the frac coords, right?
        # This corrects for VASP really annoying bug of crashing on lattices
        # which have triple product < 0. We will just invert the lattice
        # vectors.
        lattice = structure.lattice
        if numpy.linalg.det(lattice.matrix) < 0:
            lattice = Lattice(-lattice.matrix)

        # The next three lines are the lattice matrix
        # I want to use a set amount of significant figures, while is why I have
        # the odd-looking f-string
        for vector in lattice.matrix:
            vector_str = " ".join(
                f"{value:.{significant_figures}f}" for value in vector
            )
            lines.append(vector_str)

        # The next line is just a list of the elements involved.
        # Get the list of element symbols for this structure as a short string.
        # For example, a composition of Y54 C27 F53 will be converted to 'Y C F'
        # Make sure this matches the order that elements appear in the POTCAR!
        element_symbols = " ".join(
            str(element) for element in structure.composition.elements
        )
        lines.append(element_symbols)

        # The next line is site count for each of these elements
        # For example, a composition of Y54 C27 F53 will be converted to '54 27 53'
        # I need the int() because I want 54 instead of 54.0. It's a float to begin
        # with because some structures are disordered and can have partial occupancy.
        element_counts = " ".join(
            str(int(structure.composition[element]))
            for element in structure.composition.elements
        )
        lines.append(element_counts)

        # This line is only added if selective dynamics are to be included
        if add_selective_dynamics:
            lines.append("selective dynamics")

        # I assume all users want to write out in fractional coordinates
        lines.append("direct")

        # Now I iterate through the sites and add a line for each
        for site in structure:
            # start with the abc values
            # I want to use a set amount of significant figures, while is why I have
            # the odd-looking f-string
            line = " ".join(
                f"{value:.{significant_figures}f}" for value in site.frac_coords
            )
            # add a space before buidling more
            line += " "
            # if we are doing selective dynamics, grab that from the site
            # I used get incase the values have not been set, in which case the
            # values of True are assumed.
            if add_selective_dynamics:
                dynamics_tags = site.properties.get("selective dynamics")
                if dynamics_tags:
                    line += " ".join("T" if value else "F" for value in dynamics_tags)
                else:
                    line += "T T T"
                # add a space before buidling more
                line += " "
            # and lastly add the element symbol
            # BUG -- will this work if it's an oxidation-state decorated?
            line += site.specie.name
            # now add the line to our file
            lines.append(line)

        # I haven't added these features yet
        if add_velocities:
            # TODO
            raise Exception("Sorry, this isn't supported yet.")

        # Now we can join all of the lines!
        lines = "\n".join(lines) + "\n"

        # Now write the file
        # If I want a separate to_string method, I should move only this code.
        with open(filename, "w") as file:
            file.write(lines)
