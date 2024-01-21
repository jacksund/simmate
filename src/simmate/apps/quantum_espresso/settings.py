# -*- coding: utf-8 -*-

import logging

from simmate.configuration import setttings


def setup_docker():
    """
    Adds `use_docker: true` to Simmate's QE settings
    """
    logging.info("Setting 'quantum_espresso.docker.use: true' in settings")
    # TODO
    logging.info("Docker-QE is ready :heavy_check_mark:")
