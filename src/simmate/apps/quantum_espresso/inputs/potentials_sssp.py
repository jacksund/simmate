# -*- coding: utf-8 -*-

"""
We need to map which potential to grab for each element based off of the type
of calculation we are doing. To see how these were selected, you should look
at the following:

QE docs on potentials:
    https://www.quantum-espresso.org/pseudopotentials/
    https://pseudopotentials.quantum-espresso.org/
    
Standard solid-state pseudopotentials (SSSP):
    https://www.materialscloud.org/discover/sssp

Psuedo-Dojo:
    http://www.pseudo-dojo.org/index.html
"""

import json
import logging
import tarfile
import urllib

from simmate.configuration import settings
from simmate.utilities import get_directory


def setup_sssp() -> bool:
    """
    Downloads all of the SSSP potentials and mapping files needed for this app
    """
    logging.info("Setting up Standard solid-state pseudopotentials (SSSP).")
    for file_type in ["mappings", "psuedos"]:
        for psuedo_type in ["precision", "efficiency"]:
            _setup_sssp_single(file_type, psuedo_type)
    logging.info("Done!")


def _setup_sssp_single(file_type: str, psuedo_type: str):
    # we use get_dir to create the folder if it doesn't exist yet
    qe_directory = get_directory(settings.config_directory / "quantum_espresso")

    # determine which file we are trying to setup/download
    if file_type == "mappings" and psuedo_type == "precision":
        filename = "SSSP_1.3.0_PBE_precision.json"
    elif file_type == "psuedos" and psuedo_type == "precision":
        filename = "SSSP_1.3.0_PBE_precision.tar.gz"
    elif file_type == "mappings" and psuedo_type == "efficiency":
        filename = "SSSP_1.3.0_PBE_efficiency.json"
    elif file_type == "psuedos" and psuedo_type == "efficiency":
        filename = "SSSP_1.3.0_PBE_efficiency.tar.gz"

    # check if file is already present -- otherwise download it
    # TODO: I may need to switch these to a simmate CDN if I get blocked
    base_url = "https://archive.materialscloud.org/record/file?record_id=1732&filename="
    file = qe_directory / filename
    if not file.exists():
        logging.info(f"Downloading SSSP {psuedo_type} {file_type}...")
        urllib.request.urlretrieve(base_url + filename, file)
    else:
        logging.info(f"Found existing SSSP {psuedo_type} {file_type}.")

    # psuedos files are downloaded in compressed format (tar.gz). We need
    # to unpack these and move them into the /potentials folder
    if file_type == "psuedos":
        with tarfile.open(file, "r:gz") as tar:
            # Extract all contents to the specified directory
            tar.extractall(path=settings.quantum_espresso.psuedo_dir)


def _load_mappings(json_file: str):
    filename = settings.config_directory / "quantum_espresso" / json_file
    if not filename.exists():
        return {}
    with filename.open() as file:
        data = json.load(file)
    return data


SSSP_PBE_EFFICIENCY_MAPPINGS = _load_mappings("SSSP_1.3.0_PBE_efficiency.json")
SSSP_PBE_PRECISION_MAPPINGS = _load_mappings("SSSP_1.3.0_PBE_precision.json")


def check_psuedo_setup() -> bool:
    """
    Checks if SSSP psuedo files have been downloaded and are ready for use.

    To do this, we simply check that the directory has the expected files
    """

    if not SSSP_PBE_EFFICIENCY_MAPPINGS or not SSSP_PBE_PRECISION_MAPPINGS:
        return False

    # compile a list of ALL files that must be present in or for this check to
    # pass
    files = [
        "../SSSP_1.3.0_PBE_precision.json",
        "../SSSP_1.3.0_PBE_precision.tar.gz",
        "../SSSP_1.3.0_PBE_efficiency.tar.gz",
        "../SSSP_1.3.0_PBE_efficiency.tar.gz",
        *[
            mapping["filename"]
            for element, mapping in SSSP_PBE_EFFICIENCY_MAPPINGS.items()
        ],
        *[
            mapping["filename"]
            for element, mapping in SSSP_PBE_PRECISION_MAPPINGS.items()
        ],
    ]

    for file in files:
        full_filename = settings.quantum_espresso.psuedo_dir / file
        if not full_filename.exists():
            breakpoint()
            return False  # one missing is enough to exit
    # TODO: consider checking md5 hashes as well

    # if we made it to this point, then everything looks good!
    return True
