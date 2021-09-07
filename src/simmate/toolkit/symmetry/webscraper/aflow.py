# -*- coding: utf-8 -*-

from selenium import webdriver
import pandas as pd
from tqdm import tqdm

# launch the webbrowser
driver = webdriver.Chrome(
    executable_path="/snap/bin/chromium.chromedriver"
)  # /snap/bin/chromium gives errors

# load the webpage
driver.get("http://aflowlib.org/CrystalDatabase/prototype_index.html")

table = driver.find_element_by_id("myTable")

rows = table.find_elements_by_tag_name("tr")

# grab all the headers from the first row
headers = [column.text for column in rows[0].find_elements_by_tag_name("th")]
# add one extra header for the POSCAR
headers.append("POSCAR_url")

# grab all the data from the rest of the rows
data = []
for row in tqdm(rows[1:]):
    row_data = []

    for column in row.find_elements_by_tag_name("td"):
        row_data.append(column.text)

    # we need to grab the POSCAR url too
    # which we can get indirectly from the link within the first column
    href = row.find_element_by_tag_name("a").get_attribute("href")
    poscar_url = href.replace(".html", ".poscar").replace(
        "/CrystalDatabase/", "/CrystalDatabase/POSCAR/"
    )
    # append to the row data and we will go through these later - rather switch back and forth from this main page
    row_data.append(poscar_url)

    data.append(row_data)


# add a POSCAR header
headers.append("POSCAR")
# add POSCARs to each data row
for entry in tqdm(data):

    try:  # some POSCARs don't have a page... not sure why. I should contact their devs. see A_oC8_64_f.I (#179)

        # grab prototype POSCAR url
        poscar_url = entry[9]

        # move to the webpage for its POSCAR
        driver.get(poscar_url)

        # download the POSCAR string (note '\n' breaks will be there, but that's needed)
        textElement = driver.find_element_by_tag_name("pre")
        poscar = textElement.text

        # append to results
        entry.append(poscar)
    except:
        entry.append(None)


# make DataFrame
df = pd.DataFrame(data=data, columns=headers)

# close the window
driver.close()

# export to csv file
df.to_csv("aflow_prototypes.csv")

##############################################################################

# # if you want to go from a str in POSCAR format to a pymatgen structure
# # Easier method would use Structure.from_file() but we currently have just a string
# from pymatgen.io.vasp import Poscar
# input_string = textElement.text
# Poscar.from_string(input_string, False,
#                                    read_velocities=False).structure

##############################################################################
