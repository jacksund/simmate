# -*- coding: utf-8 -*-

import logging

from simmate.configuration import settings


def setup_docker():
    """
    Adds `quatum_espresso.docker.enable: true` to Simmate's QE settings
    """
    updates = {
        "quantum_espresso": {
            "docker": {
                "enable": True,
            },
        },
    }
    settings.write_updated_settings(updates)
    logging.info("Docker-QE is ready :heavy_check_mark:")
