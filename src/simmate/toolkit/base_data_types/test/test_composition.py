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


def test_chemical_subsystems(sample_compositions):

    composition = sample_compositions["Fe1"]
    assert composition.chemical_subsystems == ["Fe"]

    composition = sample_compositions["Si2"]
    assert composition.chemical_subsystems == ["Si"]

    composition = sample_compositions["C4"]
    assert composition.chemical_subsystems == ["C"]

    composition = sample_compositions["Ti2O4"]
    assert composition.chemical_subsystems == ["O", "Ti", "O-Ti"]

    composition = sample_compositions["Al4O6"]
    assert composition.chemical_subsystems == ["Al", "O", "Al-O"]

    composition = sample_compositions["Si4N4O2"]
    assert composition.chemical_subsystems == [
        "N",
        "O",
        "Si",
        "N-O",
        "N-Si",
        "O-Si",
        "N-O-Si",
    ]

    composition = sample_compositions["Si4O8"]
    assert composition.chemical_subsystems == ["O", "Si", "O-Si"]

    composition = sample_compositions["Sr4Si4N8"]
    assert composition.chemical_subsystems == [
        "N",
        "Si",
        "Sr",
        "N-Si",
        "N-Sr",
        "Si-Sr",
        "N-Si-Sr",
    ]

    composition = sample_compositions["Mg4Si4O12"]
    assert composition.chemical_subsystems == [
        "Mg",
        "O",
        "Si",
        "Mg-O",
        "Mg-Si",
        "O-Si",
        "Mg-O-Si",
    ]
