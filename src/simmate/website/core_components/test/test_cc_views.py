# -*- coding: utf-8 -*-

import pytest
from pytest_django.asserts import assertTemplateUsed

from simmate.website.core_components.templatetags.simmate_utils import structure_to_url

# BUG: disabled because the "id" column in rest api doesn't exist for this table
# @pytest.mark.django_db
# def test_spacegroup_views(client):
#     # list view
#     response = client.get("/core-components/symmetry/?format=json")
#     assert response.status_code == 200
#     # assertTemplateUsed("core_components/spacegroup.html")

#     # detail view
#     response = client.get("/core-components/symmetry/166/?format=json")
#     assert response.status_code == 200
#     # assertTemplateUsed("core_components/spacegroup.html")


@pytest.mark.django_db
def test_dummy_view(client):
    response = client.get("/core-components/test/")
    assert response.status_code == 200
    assertTemplateUsed(response, "core_components/test.html")


@pytest.mark.blender
def test_structure_viewer_view(client, structure):
    url_data = structure_to_url(structure)
    response = client.get(f"/core-components/structure-viewer/?{url_data}")
    assert response.status_code == 200
    assertTemplateUsed(response, "core_components/chem_elements/structure_viewer.html")
