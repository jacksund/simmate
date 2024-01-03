# -*- coding: utf-8 -*-

import logging
from pathlib import Path

import yaml

from simmate.utilities import get_directory

# TODO: Many of these options are hardcoded and I need a refactor on handling
# simmate settings in general. All settings will likely move to a centralized
# yaml file in the future

SIMMATE_QE_DIR = Path.home() / "simmate" / "quantum_espresso"
SIMMATE_QE_YAML = SIMMATE_QE_DIR / "settings.yaml"

if SIMMATE_QE_YAML.exists():
    with SIMMATE_QE_YAML.open() as _file:
        SIMMATE_QE_SETTINGS = yaml.full_load(_file)
else:
    SIMMATE_QE_SETTINGS = {}

DEFAULT_PSUEDO_DIR = get_directory(SIMMATE_QE_DIR / "potentials")

SIMMATE_QE_DOCKER = SIMMATE_QE_SETTINGS.get("use_docker", False)

if "default_pwscf_command" in SIMMATE_QE_SETTINGS:
    DEFAULT_PWSCF_COMMAND = SIMMATE_QE_SETTINGS["default_pwscf_command"]
elif SIMMATE_QE_DOCKER:
    DEFAULT_PWSCF_COMMAND = f"docker run -v ${{pwd}}:/qe_calc -v {DEFAULT_PSUEDO_DIR}:/potentials jacksund/quantum-espresso:v0.0.0"
else:
    DEFAULT_PWSCF_COMMAND = "pw.x < pwscf.in > pw-scf.out"


def setup_docker():
    """
    Adds `use_docker: true` to Simmate's QE settings
    """
    with SIMMATE_QE_YAML.open("w") as file:
        file.write("use_docker: true")
    logging.info(
        f"Created file {SIMMATE_QE_YAML} and added 'use_docker: true' :heavy_check_mark:"
    )
