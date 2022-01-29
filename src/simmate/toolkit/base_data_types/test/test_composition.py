# -*- coding: utf-8 -*-

import pytest

RADIUS_METHODS = [
    "ionic",
    "atomic",
    "atomic_calculated",
    "van_der_waals",
    # "metallic",  This is a special case that we test separately
    "ionic",
]


@pytest.mark.parametrize("radius_method", RADIUS_METHODS)
def test_radii_estimate(composition, radius_method):
    composition.radii_estimate(radius_method)


def test_radii_estimate_metallic(sample_compositions):

    # make sure a metallic composition succeeds
    composition_fe = sample_compositions["Fe1"]
    composition_fe.radii_estimate("metallic")

    # make sure a non-metallic composition fails
    with pytest.raises(Exception):
        composition_si = sample_compositions["Si2"]
        composition_si.radii_estimate("metallic")


@pytest.mark.parametrize("radius_method", RADIUS_METHODS)
def test_volume_estimate(composition, radius_method):
    composition.volume_estimate(radius_method)


@pytest.mark.parametrize("radius_method", RADIUS_METHODS)
def test_distance_matrix_estimate(composition, radius_method):
    composition.distance_matrix_estimate(radius_method)
