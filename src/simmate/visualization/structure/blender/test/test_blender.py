# -*- coding: utf-8 -*-

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

# @pytest.mark.blender  -- this test requires blender to NOT be installed
def test_get_blender_command():
    pytest.raises(BlenderNotInstalledError, get_blender_command)
