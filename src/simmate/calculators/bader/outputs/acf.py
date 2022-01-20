# -*- coding: utf-8 -*-

import pandas


def ACF(filename="ACF.dat"):

    # open the file, grab the lines, and then close it
    with open(filename) as file:
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

    return dataframe, extra_data
