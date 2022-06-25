# -*- coding: utf-8 -*-

import platform

import pytest

from simmate.visualization.structure.blender.configuration import (
    get_blender_command,
    BlenderNotInstalledError,
)

# Requires blender install which is not possible in CI yet.
#
# from simmate.visualization.structure.blender.base import (
#     make_blender_structure,
#     serialize_structure_sites,
# )


@pytest.mark.blender  # this test requires blender to NOT be installed
def test_get_blender_command():

    operating_system = platform.system()

    if operating_system == "Darwin":
        pytest.raises(NotImplementedError, get_blender_command)
    else:
        pytest.raises(BlenderNotInstalledError, get_blender_command)
