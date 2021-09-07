# -*- coding: utf-8 -*-

##############################################################################

"""

IMPORTANT!!!

We can't use the biblao server for our wyckoff data.

This is because a number of spacegroups are written based off of the wrong lattice.

For example, spacegroup 166 is written with the hexagonal lattice vectors, which
makes the smallest multiplicity 3 among all wy_sites. This in turn makes it so 
there is no possible wyckoff group combination that gives 2:1 stoich -- this is
misleading because we know that Ca2N has the spacegroup 166

"""

##############################################################################


from selenium import webdriver
import pandas as pd
from tqdm import tqdm

# launch the webbrowser
driver = webdriver.Chrome(
    executable_path="/snap/bin/chromium.chromedriver"
)  # /snap/bin/chromium gives errors

table_info = []
for spacegroup in tqdm(range(1, 231)):

    # load the webpage
    driver.get("https://www.cryst.ehu.es/cryst/get_wp.html")

    # find the input element (it should be empty to start, otherwise use inputElement.clear())
    inputElement = driver.find_element_by_name("gnum")

    # fill the input element with the spacegroup number
    inputElement.send_keys(spacegroup)

    # click the button that says "Standard/Defualt Settings"
    driver.find_element_by_name("standard").click()

    table = driver.find_elements_by_tag_name("table")[
        1
    ]  # grab all tables and then the one we want is the 2nd
    rows = table.find_elements_by_tag_name(
        "tr"
    )  # grab all the rows in that table. Note some rows have a table (w. more rows) inside so this isn't ideal.

    # first row is the table headers # THIS DOESNT NEED TO BE DONE EVERY TIME - consider moving for speed up
    headers = rows[0].text
    # remove the "\n" characters
    headers = headers.replace("\n", "")
    # split the string into a list at each ' '
    headers = headers.split(" ")
    # I'd like the first header to be the spacegroup
    headers = ["SpaceGroup", headers[0], headers[1], headers[2], headers[3]]

    # the second row is a spacer (empty)
    # then after that it's a mixture of the full row that we want with some duplicate "rows" (the last column)
    for row in rows[2:]:

        # grab the string
        info = row.text
        # remove the "\n" characters
        info = info.replace("\n", " ")
        # split the string into a list at each ' '
        info = info.split(" ")

        # this split() sometimes gives us the incorrect result because the entry in Sitesymmetry column might have a space in it
        # spacegroup 229 for example, wy_site 'g' has Sitesymmetry='mm2 . .' and wy_site 'd' has Sitesymmetry='-4m. 2'
        # to fix this, I look at at the indicies immediately following the typical Sitesymmetry position (at index=2)
        # and if that index has an entry length smaller than 3, I deem it part of the Sitesymmetry.
        # This works because (x,y,z) will have length >= 7
        # This code is pretty ugly... But we are just webscraping and formmatting data the way we want, so oh well!
        info_fixed = []
        for i, entry in enumerate(info):
            # first two entries of "Multiplicity" and "Wyckoffletter" are fine - just append them
            if i == 0 or i == 1:
                info_fixed.append(entry)
            # index 2 is the start of the "Sitesymmetry" entry
            elif i == 2:
                # look at the next 2 entries (this issue never goes past two spaces in the Sitesymmetry label)
                # and evaluate whether or not they should be apart of the Sitesymmetry label (see logic explained above)
                # sometimes there is no index at info[i+1], so check the len first!
                if len(info) > 3:
                    next1 = info[i + 1]
                    if len(next1) < 3:
                        entry += " " + next1
                # sometimes there is no index at info[i+2], so check the len first!
                if len(info) > 4:
                    next2 = info[i + 2]
                    if len(next2) < 3:
                        entry += " " + next2
                # entry should now be the correct label for SiteSymmetry so append it
                info_fixed.append(entry)
            # for these two indecies, only append if they are not a part of the SiteSymmetry label
            elif i == 3 or i == 4:
                if len(entry) > 3:
                    info_fixed.append(entry)
            # the rest of the entries we can safely assume are coordinates
            else:
                info_fixed.append(entry)
        # take these fixes and override the original info
        info = info_fixed

        # we need to check if this is actually a row we want.
        # the logic I use here is that the multiplicity won't ever be more than 3 digits (max is 192)
        # while the an (x,y,z) entry will alway have more than 3
        # so therefore the first column should be =< 3 if it's a row we want
        if len(info[0]) <= 3:
            # the first 3 entries match the first 3 headers of the table
            # the rest should go under the 4th header. Let's move them all in to one entry.
            info = [spacegroup, int(info[0]), info[1], info[2], info[3:]]

            # reformat the '(x,y,z)' strings in info[4] list to ['x','y','z']
            # info[4] = [n[1:-1].split(',') for n in info[4]]

            # add the result to the dataframe
            table_info.append(info)

# close the window
driver.close()

# make DataFrame
df = pd.DataFrame(data=table_info, columns=headers)

# export to csv file
df.to_csv("wyckoffdata.csv", index=False)

##############################################################################

# set this if you want to run headless (i.e. in the background)
# options = webdriver.ChromeOptions()
# options.headless = True
# and then add the setting to this call: webdriver.Chrome(options = options)


# customize the window if you'd like
# driver.minimize_window()
# driver.set_window_size(width=1920, height=1080)

##############################################################################
