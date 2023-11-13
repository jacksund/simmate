# -*- coding: utf-8 -*-

from pathlib import Path

import pandas
from pymatgen.io.vasp import Potcar
from pymatgen.io.vasp.outputs import Chgcar


def ACF(directory: Path = None, filename="ACF.dat"):
    # grab working directory if one wasn't provided
    if not directory:
        directory = Path.cwd()

    # convert to path obj
    filename = directory / filename

    # open the file, grab the lines, and then close it
    with filename.open() as file:
        lines = file.readlines()

    # establish the headers. Note that I ignore the '#' column as this is
    # just site index.
    headers = ("x", "y", "z", "charge", "min_dist", "atomic_vol")

    # create a list that we will load data into
    bader_data = []
    # The first 2 lines are header and the final 4 lines are the footer. This is always
    # true so we don't need to iterate through those. The data we want is between the
    # header and footer so that's what we loop through.
    for line in lines[2:-4]:
        # By running strip, we convert the line from a string to a list of
        # The values are all still strings, so we convert them to int/floats
        # before saving. I add [1:] because the first value is just '#' which
        # is site index and we dont need.
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

    # The remaining code is to analyze the results and calculate extra
    # information such as the final oxidation states. This requires extra
    # files to be present, such as from a vasp calculation

    potcar_filename = directory / "POTCAR"
    chgcar_filename = directory / "CHGCAR"
    chgcar_empty_filename = directory / "CHGCAR_empty"  # SPECIAL CASE

    # check if the required vasp files are present before doing the workup
    if potcar_filename.exists() and (
        chgcar_filename.exists() or chgcar_empty_filename.exists()
    ):
        # load the electron counts used by VASP from the POTCAR files
        # OPTIMIZE: this can be much faster if I have a reference file
        potcars = Potcar.from_file(potcar_filename)
        nelectron_data = {}
        # the result is a list because there can be multiple element potcars
        # in the file (e.g. for NaCl, POTCAR = POTCAR_Na + POTCAR_Cl)
        for potcar in potcars:
            nelectron_data.update({potcar.element: potcar.nelectrons})

        # SPECIAL CASE: in scenarios where empty atoms are added to the structure,
        # we should grab that modified structure instead of the one from the POSCAR.
        # the empty file will always take preference
        if chgcar_empty_filename.exists():
            chgcar = Chgcar.from_file(chgcar_empty_filename)
            structure = chgcar.structure
            # We typically use helium ("He") as the empty atom, so we will
            # need to add this to our element list for oxidation analysis.
            # We use 0 for electron count because this is an 'empty' atom, and
            # not actually Hydrogen
            nelectron_data.update({"He": 0})

        # otherwise, grab the structure from the CHGCAR
        # OPTIMIZE: consider grabbing from the POSCAR or CONTCAR for speed
        else:
            chgcar = Chgcar.from_file(chgcar_filename)
            structure = chgcar.structure

        # Calculate the oxidation state of each site where it is simply the
        # change in number of electrons associated with it from vasp potcar vs
        # the bader charge I also add the element strings for filtering functionality
        elements = []
        oxi_state_data = []
        for site, site_charge in zip(structure, dataframe.charge.values):
            element_str = site.specie.name
            elements.append(element_str)
            oxi_state = nelectron_data[element_str] - site_charge
            oxi_state_data.append(oxi_state)

        # add the new column to the dataframe
        dataframe = dataframe.assign(
            oxidation_state=oxi_state_data,
            element=elements,
        )
        # !!! There are multiple ways to do this, but I don't know which is best
        # dataframe["oxidation_state"] = pandas.Series(
        #     oxi_state_data, index=dataframe.index)

    return dataframe, extra_data
