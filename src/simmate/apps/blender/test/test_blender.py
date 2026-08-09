# -*- coding: utf-8 -*-

import platform

import pytest

from simmate.apps.blender.config import (
    BlenderNotInstalledError,
    get_blender_command,
)


@pytest.mark.blender  # this test requires blender to NOT be installed
def test_get_blender_command():
    operating_system = platform.system()

    if operating_system == "Darwin":
        pytest.raises(NotImplementedError, get_blender_command)
    else:
        pytest.raises(BlenderNotInstalledError, get_blender_command)
