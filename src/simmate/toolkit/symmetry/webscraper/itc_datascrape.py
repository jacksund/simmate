# -*- coding: utf-8 -*-

"""

Currently I grab the first table for each spacegroup, but in many cases there 
are more options. For example, spacegroup 10 has "Unique Axis b" and "Unique 
Axis c" tables to choose from -- by default I grab the first. The same goes for
spacegroups like 166 where there is a "Hexagonal" and "Rhombohedral" option. 
If instead I wanted to specify which to choose, I would look instead the headers
on each page. The headers should line up with the tables. For example in
spacegroup 166, I can see:
    if "HEXAGONAL AXES" in header.text

"""


from selenium import webdriver
import pandas as pd
from tqdm import tqdm

# launch the webbrowser
driver = webdriver.Chrome(
    executable_path="/snap/bin/chromium.chromedriver"
)  # /snap/bin/chromium gives errors

asym_data = []
wy_data = []
for spacegroup in tqdm(range(1, 231)):

    # change the int spacegroup to a string in three digit format
    # for example, 15 will turn into 015 and 1 will turn into 001
    sg_format = (
        f"{spacegroup:03}"  # I don't understand f-string formatting yet but this works
    )

    # make our target url
    target_url = "https://it.iucr.org/Ab/ch7o1v0001/sgtable7o1o" + sg_format + "/"

    # load the webpage
    driver.get(target_url)

    ###### Grab the asymmetric unit data ######

    # In many cases there are multiple tables becuase there are multiple ways to draw a lattice
    # For example, spacegroup 10 has two options: "UNIQUE AXIS b" and "UNIQUE AXIS c"
    # I still don't fully understand why there are two in this case
    # this issue more clear when looking at spacegroup 166, which has two options: "HEXAGONAL AXES" and "RHOMBOHEDRAL AXES"
    # In all cases except for when it's hex vs. rhomb, we want the first table

    # first grab everything labeled with class="asymmetricunit"
    elements = driver.find_elements_by_class_name("asymmetricunit")
    # then limit these elements to those that possess the <table> tag
    tables = [element for element in elements if element.tag_name == "table"]
    # grab everything labeled with class="sgheader"
    elements = driver.find_elements_by_class_name("sgheader")
    # then limit these elements to those that possess the <div> tag
    headers = [element for element in elements if element.tag_name == "div"]
    # we can use the header to check for which cell type / unique axis table we want
    # but for now, we are just grabbing the first table
    target = 0
    # grab the header for our target table and make it into a list of strings
    header = headers[target].text.split("\n")
    # cell specification is only in some cases (i.e. a third row doesn't always exist)
    if len(header) > 2:
        cell_spec = header[2]
    else:
        cell_spec = None
    # the data we want is in the 2nd cell of the 1st table
    data = tables[target].find_elements_by_tag_name("td")[1].text
    # append to output list
    asym_data.append([spacegroup, data, cell_spec])

    ###### Grab the wyckoff site data ######

    # we are following the same rules as with the asymmetric data above (first table unless its hexagonal)
    # There are two table we are grabbing from here -- genpos as well as specpos

    # first grab everything labeled with class="genpos"
    elements = driver.find_elements_by_class_name("genpos")
    # then limit these elements to those that possess the <table> tag
    tables = [element for element in elements if element.tag_name == "table"]
    # grab everything labeled with class="sgheader"
    elements = driver.find_elements_by_class_name("sgheader")
    # then limit these elements to those that possess the <div> tag
    headers = [element for element in elements if element.tag_name == "div"]
    # we can use the header to check for which cell type / unique axis table we want
    # but for now, we are just grabbing the first table
    target = 0
    # grab the header for our target table and make it into a list of strings
    header = headers[target].text.split("\n")
    # grab all of the rows in the 1st table
    rows = tables[target].find_elements_by_tag_name("tr")
    # we only want rows with class="specpos"
    # and we are looking specifically at the text
    rows = [row.text for row in rows if row.get_attribute("class") == "specpos"]
    # the first row is the header so skip it
    for row in rows[1:]:
        # change characters in the string and then split it into a list
        row_content = row.replace("\n", " ").split(" ")
        # there is a bug for spacegroup 47, because its letter is alpha - which doesnt show up
        if spacegroup == 47:
            row_content.insert(1, "A")
        # first index is Multiplicity
        mult_conv = int(row_content[0])
        # second index is Wyckoffletter
        # third is Sitesymmetry -- which for general positions is always 1
        letter, sym = row_content[1:3]
        # fifth through seventh are the coords -- which for general is always (x,y,z)
        coords = row_content[4] + row_content[5] + row_content[6]
        coords = coords.replace("2x", "2*x")
        # Note the that the current Multiplicity indicated is for the convential cell
        # where we'd like to know the primitive cell's multiplicity
        # The letters marked below correspond to the following:
        # P primitive
        # I body centered
        # F face centered
        # A centered on A faces only
        # B centered on B faces only
        # C centered on C faces only
        # R rhombohedral
        # I grab this information from PyXtal's crystal.py file.
        if spacegroup in [
            22,
            42,
            43,
            69,
            70,
            196,
            202,
            203,
            209,
            210,
            216,
            219,
            225,
            226,
            227,
            228,
        ]:
            mult_prim = mult_conv / 4  # F
        elif spacegroup in [146, 148, 155, 160, 161, 166, 167]:
            mult_prim = mult_conv / 3  # R
        elif spacegroup in [
            5,
            8,
            9,
            12,
            15,
            20,
            21,
            23,
            24,
            35,
            36,
            37,
            38,
            39,
            40,
            41,
            44,
            45,
            46,
            63,
            64,
            65,
            66,
            67,
            68,
            71,
            72,
            73,
            74,
            79,
            80,
            82,
            87,
            88,
            97,
            98,
            107,
            108,
            109,
            110,
            119,
            120,
            121,
            122,
            139,
            140,
            141,
            142,
            197,
            199,
            204,
            206,
            211,
            214,
            217,
            220,
            229,
            230,
        ]:
            mult_prim = mult_conv / 2  # A, C, I
        else:
            mult_prim = mult_conv / 1  # P
        # append to output list
        wy_data.append([spacegroup, mult_conv, mult_prim, letter, sym, coords])

    # now grab everything labeled with class="specpos"
    elements = driver.find_elements_by_class_name("specpos")
    # then limit these elements to those that possess the <table> tag
    tables = [element for element in elements if element.tag_name == "table"]
    # if there are no tables, jump to the next spacegroup (this happens with spacegroup 1)
    if not tables:
        continue
    # grab everything labeled with class="sgheader"
    elements = driver.find_elements_by_class_name("sgheader")
    # then limit these elements to those that possess the <div> tag
    headers = [element for element in elements if element.tag_name == "div"]
    # we can use the header to check for which cell type / unique axis table we want
    # but for now, we are just grabbing the first table
    target = 0
    # grab the header for our target table and make it into a list of strings
    header = headers[target].text.split("\n")
    # grab all of the rows in the 2nd table
    rows = tables[target].find_elements_by_tag_name("tr")
    # we only want rows with class="specpos"
    # and we are looking specifically at the text
    rows = [row for row in rows if row.get_attribute("class") == "specpos"]
    # the first row is the header so skip it
    for row in rows[1:]:
        # grab the text; change characters in the string; and then split it into a list
        row_content = row.text.replace("\n", " ").split(" ")
        # first index is Multiplicity
        mult_conv = int(row_content[0])
        # second index is Wyckoffletter
        letter = row_content[1]
        # fourth and the ones that follow are Sitesymmetry
        # # third is empty and Sitesymmtry label ends at the next empty
        sym = ""
        i = 3
        while row_content[i] != "":
            sym += row_content[i]
            i += 1
        # in order to grab the coordinates, we need to look at all the entries inside of the row
        row_elements = row.find_elements_by_tag_name("td")
        # and we want the elements specifically with class='specposcoords'
        row_elements = [
            element
            for element in row_elements
            if element.get_attribute("class") == "specposcoords"
        ]
        # and the coords that we are interested in should be the first entry
        # I also want to remove the spaces in the coords
        coords = row_elements[0].text.replace(" ", "").replace("2x", "2*x")
        # Note the that the current Multiplicity indicated is for the convential cell
        # where we'd like to know the primitive cell's multiplicity
        # The letters marked below correspond to the following:
        # P primitive
        # I body centered
        # F face centered
        # A centered on A faces only
        # B centered on B faces only
        # C centered on C faces only
        # R rhombohedral
        # I grab this information from PyXtal's crystal.py file.
        if spacegroup in [
            22,
            42,
            43,
            69,
            70,
            196,
            202,
            203,
            209,
            210,
            216,
            219,
            225,
            226,
            227,
            228,
        ]:
            mult_prim = mult_conv / 4  # F
        elif spacegroup in [146, 148, 155, 160, 161, 166, 167]:
            mult_prim = mult_conv / 3  # R
        elif spacegroup in [
            5,
            8,
            9,
            12,
            15,
            20,
            21,
            23,
            24,
            35,
            36,
            37,
            38,
            39,
            40,
            41,
            44,
            45,
            46,
            63,
            64,
            65,
            66,
            67,
            68,
            71,
            72,
            73,
            74,
            79,
            80,
            82,
            87,
            88,
            97,
            98,
            107,
            108,
            109,
            110,
            119,
            120,
            121,
            122,
            139,
            140,
            141,
            142,
            197,
            199,
            204,
            206,
            211,
            214,
            217,
            220,
            229,
            230,
        ]:
            mult_prim = mult_conv / 2  # A, C, I
        else:
            mult_prim = mult_conv / 1  # P
        # append to output list
        wy_data.append([spacegroup, mult_conv, mult_prim, letter, sym, coords])

# close the window
driver.close()

#####

# make Asym DataFrame
df_asym = pd.DataFrame(
    data=asym_data, columns=["spacegroup", "asymmetricunit", "cellspec"]
)
# export to csv file
df_asym.to_csv("asymdata.csv", index=False)

#####

# make Asym DataFrame
df_wy = pd.DataFrame(
    data=wy_data,
    columns=[
        "SpaceGroup",
        "MultiplicityConventional",
        "MultiplicityPrimitive",
        "Wyckoffletter",
        "Sitesymmetry",
        "Coordinates",
    ],
)
# export to csv file
df_wy.to_csv("wyckoffdata.csv", index=False)

##############################################################################

# set this if you want to run headless (i.e. in the background)
# options = webdriver.ChromeOptions()
# options.headless = True
# and then add the setting to this call: webdriver.Chrome(options = options)


# customize the window if you'd like
# driver.minimize_window()
# driver.set_window_size(width=1920, height=1080)

##############################################################################
