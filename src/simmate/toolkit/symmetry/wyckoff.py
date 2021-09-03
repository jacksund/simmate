# -*- coding: utf-8 -*-

##############################################################################

import os
import pandas as pd
import itertools

##############################################################################


def loadWyckoffData():

    """
    This function loads the csv file containing all wyckoff site data into
    a pandas dataframe. One column that we need is not directly stored in
    the csv file though - this is site "Availablility", which can be inferred
    from the "Coordinates" column. Therefore, this function generates the
    "Availability" column before returning the pandas dataframe.
    """

    # Grab the directory of this current python file
    current_directory = os.path.dirname(__file__)

    # Set the full path to the data csv file
    datafile = current_directory + "/wyckoffdata.csv"

    # Load the csv file into a pandas dataframe
    data = pd.read_csv(datafile)

    # We need "Availibility" of each site as a column of the dataframe.
    # This can be found using the "Coordinates" column:
    # A wycloff site can only be used once (i.e. 0,0,0)
    # or an infinite number of times (i.e x,y,z).
    avail = []
    # Iterate through each site.
    for wy_site in data["Coordinates"].values:  # .values grabs column as numpy
        # The wy_site can be used infinite number of times if there
        # is a x,y, or z coordinate available.
        if any(i in wy_site for i in "xyz"):
            availability = float("inf")
        # The wy_site can only be used once if there
        # is no x,y, or z in the coordinates.
        else:
            availability = 1
        avail.append(availability)
    # We now have the final list and can add the new column to the dataframe.
    data["Availability"] = avail

    # return the data
    return data


##############################################################################


def findValidWyckoffCombos(stoich, spacegroup, wy_data=loadWyckoffData()):

    """
    Given a composition's stoichiometry (such as [4,4,12] for Mg4Si4O12) and
    a single spacegroup (1-230), this function will find all valid wyckoff
    combinations that can produce that stoichiometry.

    stoich = a list of integers representing the target stoichiometry
    spacegroup = an integer for the target spacegroup
    wy_data = pandas dataframe with wyckoff data (DON'T EDIT THIS!)

    NOTE: don't change the wy_data input! It is set in the header instead of
    running inside the function for time performance reasons. By putting it
    in the header, calling findValidWyckoffCombos() repetitively will not
    repetitively call loadWyckoffData() which yields a massive
    speed improvement.
    """

    # Grab all the wyckoff sites associated with the spacegroup given
    wy_sg = wy_data.query("SpaceGroup == @spacegroup")

    # This separate wy_sites into unique (MultiplicityPrimitive, Availability)
    # groups. This is useful for massive speed-up in the function as we can
    # find combos of these groups instead of all wy_sites. For example, all
    # wy_sites with Multiplicity = 2 and Availability = 2 will be treated as
    # one group when making combos then when that combo is used (in a
    # different function), it randomly grabs one wy_site from the group.
    wy_groups = wy_sg.groupby(["MultiplicityPrimitive", "Availability"]).groups

    # First, we need to find what the valid combinations are for each of the
    # individual elements. This code finds all combinations of wyckoffs sites.
    # Combinations can be up to nsites. So we go through all combinations
    # and see which ones meet the following criteria:
    #   1) total wyckoff sites used is less than nsites
    #   2) the total multiplicity of all wyckoff sites is equal to nsites
    #   3) no wyckoff site with an availability of 1 is used multiple times
    wy_combos = []
    for i, nsites in enumerate(stoich):
        # Don't search for wyckoff combinations if it's already been done for
        # a given nsite size. In [4,4,12] example, we run this code for
        # nsites=4 twice, which is unneccessary. Instead, we want to copy the
        # result of the first run, which is much faster. This IF statement
        # (and all code in it) is therefore a shortcut. The algorithm works
        # the same without this check, just slower.
        if nsites in stoich[:i]:  # if nsites value is earlier in stoich list
            # Find where in stoich that the nsites was done before
            i_match = stoich.index(nsites)
            # The index of the first occurence in stoich will match the
            # index in wy_combos. Copy the result of that wy_combo result over.
            wy_combos.append(wy_combos[i_match])
            # then skip to the next nsites
            continue
        # Make an empty list that we can store all the valid combinations in
        valid_group_combos = []
        # Try each combination size up to the value of nsite
        for s in range(1, nsites + 1):  # +1 because range stops at value prior
            # Find all combinations at the combo size of s
            combos = itertools.combinations_with_replacement(wy_groups, s)
            # For each combination, check that criteria are met
            for combo in combos:
                # Say the combo is valid until proven otherwise
                is_valid = True
                # The total multiplicity of all wyckoff sites must be equal to
                # nsites. Note, index 0 is "MultiplicityPrimitive".
                mults = sum([wy_group[0] for wy_group in combo])
                if mults != nsites:
                    # No need to check further, so jump to the next combo.
                    continue  # same as is_valid=False, but faster
                # No wy_site with an availability of 1 can used multiple times.
                # For example, site 0,0,0 cant be used more than once.
                for wy_group in combo:
                    # The 'uses' is total times that a given wy_group is used
                    uses = combo.count(wy_group)
                    # The 'avail_s' is the availabilitiy of a single wy_site
                    # in the wy_group, which is either 1 or infinite (inf).
                    avail_s = wy_group[1]
                    # If a single wy_site in the group has Availability = 1
                    if avail_s == 1:
                        # The total times that a wy_group is allowed to be
                        # used is the length of the group. For example, the
                        # group of 6 wy_sites that have Availability = 1 can
                        # be used a maximum of 6 times.
                        avail_g = wy_groups[wy_group].size
                    # If a single wy_site in the group has Availability = inf
                    else:
                        # The total times that this group can be used is inf.
                        # Note index 1 grabs the'inf' availability value.
                        avail_g = wy_group[1]
                    # Now check if the site is overused.
                    if uses > avail_g:
                        is_valid = False
                        break  # no need to check further in this combo
                # If the combo has passed all tests if it reached this point,
                # then add it to the valid list.
                if is_valid:
                    valid_group_combos.append(combo)
        wy_combos.append(valid_group_combos)

    # We now need to find the unique combinations of wy_combos accross all
    # elements. For example, we ensure that Mg and Si both can't use 0,0,0.
    # Make an empty list that we can store all the valid combinations in
    valid_combos = []
    #!!! The "*" uses "star expression, which I don't fully understand but it
    #!!! gives the desired output that I want.
    combos = itertools.product(*wy_combos)
    for combo in combos:
        # say the combo is valid until proven otherwise
        is_valid = True
        # The combo is invalid if a wycoff sites use is more than it's total
        # availibility. For example, the wyckoff site of (0,0,0) cannot be
        # used by both Mg and Si, whereas the wyckoff site of (0,0,z) can be
        # used by multiple elements.
        for wy_group in wy_groups:
            # The 'uses' is total times that a given wy_group is used
            uses = sum([element.count(wy_group) for element in combo])
            # The 'avail_s' is the availabilitiy of a single wy_site
            # in the wy_group, which is either 1 or infinite (inf).
            avail_s = wy_group[1]
            # If a single wy_site in the group has Availability = 1
            if avail_s == 1:
                # The total times that a wy_group is allowed to be
                # used is the length of the group. For example, the
                # group of 6 wy_sites that have Availability = 1 can
                # be used a maximum of 6 times.
                avail_g = wy_groups[wy_group].size
            # If a single wy_site in the group has Availability = inf
            else:
                # The total times that this group can be used is inf.
                # Note index 1 grabs the'inf' availability value.
                avail_g = wy_group[1]
            if uses > avail_g:
                is_valid = False
                break  # no need to check further in this combo
        # If the combo has passed all tests if it reached this point,
        # then add it to the valid list.
        if is_valid:
            valid_combos.append(combo)
    # We want to return the valid combinations of wyckoff groups because
    # groups can refer to a number of wy_sites (a,b,c, etc.)
    #!!! TO-DO: add a better explanation of what's being returned here
    return {"WyckoffGroups": wy_groups, "ValidCombinations": valid_combos}


##############################################################################


def findValidWyckoffCombosForListofSpacegroups(
    stoich, sg_include=range(1, 231), sg_exclude=[]
):

    """
    Find all wyckoff group combinations for specified list of spacegroups.
    This function calls the findValidWyckoffCombos function repeatedly, so
    really this is just a convience function.

    stoich = list of nsites for each element
        (i.e. Mg4Si4O12 has stoich = [4,4,12])
    sg_include = list of spacegroups that we are interested in.
        (default is all 230 spacegroups)
    sg_exclude = list of spacegroups that we should explicitly ignore
    """

    # Combine the inputs into a list of spacegroups we need to investigate
    sg_to_search = [sg for sg in sg_include if sg not in sg_exclude]

    # We save the outputs as a dictionary where the spacegroup (integer) is
    # the key to combo results.
    #!!! Consider changing this to a list where index=spacegroup-1
    combos_by_sg = {}
    for spacegroup in sg_to_search:
        combos = findValidWyckoffCombos(stoich, spacegroup)
        combos_by_sg.update({spacegroup: combos})

    return combos_by_sg


##############################################################################


def loadAsymmetricUnitData():

    """
    This function simply loads the csv file containing all asymmetric unit
    data into a pandas dataframe. It then just grabs the column we need and
    turns it into a numpy array (for performance reasons) even though we lose
    the spacegroup column - it's really just index+1 for each entry.
    """

    # grab the directory of this current python file
    current_directory = os.path.dirname(__file__)

    # set the full path to the data csv file
    datafile = current_directory + "/asymdata.csv"

    # load the csv file into a pandas dataframe
    data = pd.read_csv(datafile)

    # for speed, limit output to just a numpy array of the asym column
    data = data["asymmetricunit"].values

    # return the data
    return data


##############################################################################


def loadSpecifiedUnitData():

    """
    THIS IS JUST A COPY/PASTE OF loadAsymmetricUnitData() WITH A DIFFERENT
    COLUMN GRAB I NEED TO UPDATE THESE CSV FILES OR COMBINE THESE FUNCTIONS.
    """

    current_directory = os.path.dirname(__file__)
    datafile = current_directory + "/asymdata.csv"
    data = pd.read_csv(datafile)
    data = data["cellspec"].values
    return data


##############################################################################
